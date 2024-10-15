import datetime
import zoneinfo
from abc import abstractmethod
from pathlib import Path
from typing import Annotated, Callable, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic_extra_types.timezone_name import TimeZoneName

from acoupi import components, data, tasks
from acoupi.components import types
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.programs.core import (
    DEFAULT_WORKER_CONFIG,
    AcoupiProgram,
    NoUserPrompt,
)
from acoupi.system.files import get_temp_dir


## ---------- Step 1 - Components Configuration ---------- ##
## Define the configuration schema for the program, which
## include configuration for compoment setup and task creation.
## ------------------------------------------------------- ##
class AudioConfiguration(BaseModel):
    """Audio recording configuration schema."""

    duration: int = 3
    interval: int = 12
    chunksize: Annotated[int, NoUserPrompt] = 8192
    schedule_start: datetime.time = Field(
        default=datetime.time(hour=8, minute=0, second=0)
    )
    schedule_end: datetime.time = Field(
        default=datetime.time(hour=20, minute=0, second=0)
    )


class MessagingConfig(BaseModel):
    """Message configuration schema."""

    db_messages: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "messages.db",
    )
    message_send_interval: int = 120
    http: Optional[components.HTTPConfig] = None
    mqtt: Optional[components.MQTTConfig] = None


class PathsConfiguration(BaseModel):
    """Data configuration schema."""

    tmp_audio: Path = Field(default_factory=get_temp_dir)
    recordings: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "recordings",
    )
    cprofile_detection: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "cprofile_detection.prof",
    )
    cprofile_management: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "cprofile_management.prof",
    )
    cprofile_messaging: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "cprofile_messaging.prof",
    )
    db_metadata: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "metadata.db",
    )


## ---------- Step 2 - Program Configuration ---------- ##
## Define the program configuration schema. Take the specific
## configuration of the above components.
## ---------------------------------------------------- ##
class cProfileProgram_Configuration(BaseModel):

    timezone: TimeZoneName = Field(default=TimeZoneName("Europe/London"))
    microphone: MicrophoneConfig
    recording: AudioConfiguration = AudioConfiguration()
    paths: PathsConfiguration = Field(default_factory=PathsConfiguration)
    messaging: MessagingConfig = MessagingConfig()


ProgramConfig = TypeVar("ProgramConfig", bound=cProfileProgram_Configuration)


class cProfileProgram(AcoupiProgram[ProgramConfig]):

    worker_config = DEFAULT_WORKER_CONFIG
    model: types.Model
    recorder: types.AudioRecorder
    store: types.Store
    messenger: Optional[types.Messenger]
    message_store: types.MessageStore

    def setup(self, config: ProgramConfig) -> None:
        self.validate_dirs(config)
        self.recorder = self.configure_recorder(config)
        self.model = self.configure_model(config)
        self.store = self.configure_store(config)
        self.message_store = self.configure_message_store(config)
        self.messenger = self.configure_messenger(config)
        self.register_recording_task(config)
        self.register_file_management_task(config)
        self.register_messaging_task(config)
        super().setup(config)

    def validate_dirs(self, config: ProgramConfig):
        if not config.paths.tmp_audio.exists():
            config.paths.tmp_audio.mkdir(parents=True)
        if not config.paths.recordings.exists():
            config.paths.recordings.mkdir(parents=True)
        if not config.paths.db_metadata.parent.exists():
            config.paths.db_metadata.parent.mkdir(parents=True)
        if not config.messaging.db_messages.parent.exists():
            config.messaging.db_messages.parent.mkdir(parents=True)

    def on_start(self, deployment: data.Deployment):
        self.store.store_deployment(deployment)
        super().on_start(deployment)

    def on_end(self, deployment: data.Deployment):
        self.store.update_deployment(deployment)
        super().on_end(deployment)

    def check(self, config: ProgramConfig):
        recorder_check = getattr(self.recorder, "check", None)
        if callable(recorder_check):
            recorder_check()
        model_check = getattr(self.model, "check", None)
        if model_check and callable(model_check):
            model_check()
        super().check(config)

    ## ---------- Step 4 - Assign Config to each components ---------- ##
    def configure_recorder(self, config) -> types.AudioRecorder:
        microphone = config.microphone
        return components.PyAudioRecorder(
            duration=config.recording.duration,
            samplerate=microphone.samplerate,
            audio_channels=microphone.audio_channels,
            device_name=microphone.device_name,
            chunksize=config.recording.chunksize,
            audio_dir=config.paths.tmp_audio,
        )

    @abstractmethod
    def configure_model(self, config: ProgramConfig) -> types.Model:
        """Configure the detection model."""

    def configure_store(self, config: ProgramConfig) -> types.Store:
        return components.SqliteStore(config.paths.db_metadata)

    def configure_message_store(self, config: ProgramConfig) -> types.MessageStore:
        return components.SqliteMessageStore(config.messaging.db_messages)

    def configure_messenger(self, config: ProgramConfig):
        if config.messaging.http is not None:
            return components.HTTPMessenger.from_config(config.messaging.http)
        if config.messaging.mqtt is not None:
            return components.MQTTMessenger.from_config(config.messaging.mqtt)
        return None

    ## ---------- Step 5 - Create and regsiter tasks ---------- ##
    def register_recording_task(self, config: ProgramConfig):

        recording_task = tasks.generate_recording_task(
            recorder=self.recorder,
            store=self.store,
            logger=self.logger.getChild("recording"),
            recording_conditions=self.get_recording_conditions(config),
        )

        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(seconds=config.recording.interval),
            callbacks=self.get_recording_callback(config),
            queue="recording",
        )

    def create_detection_task(self, config: ProgramConfig):
        # cprofile_detection_task = tasks.cprofile_create_detection_task(
        detection_task = tasks.generate_detection_task(
            store=self.store,
            model=self.model,
            message_store=self.message_store,
            logger=self.logger.getChild("detection"),
            output_cleaners=self.get_output_cleaners(config),
            processing_filters=self.get_processing_filters(config),
            message_factories=self.get_message_factories(config),
        )

        # return cprofile_detection_task
        return detection_task

    def get_recording_callback(self, config) -> list[Callable]:
        return [self.create_detection_task(config)]

    def register_messaging_task(self, config: ProgramConfig):
        if self.messenger is None:
            return

        # cprofile_messaging_task = tasks.cprofile_create_messaging_task(
        messaging_task = tasks.generate_send_messages_task(
            message_store=self.message_store,
            messengers=[self.messenger],
            logger=self.logger.getChild("messaging"),
            # cprofile_output=config.paths.cprofile_messaging,
        )

        self.add_task(
            # function=cprofile_messaging_task,
            function=messaging_task,
            schedule=config.messaging.message_send_interval,
            queue="celery",
        )

    def register_file_management_task(self, config: ProgramConfig):
        cprofile_management_task = tasks.cprofile_create_management_task(
            store=self.store,
            logger=self.logger.getChild("file_management"),
            file_managers=self.get_recording_saving_managers(config),
            file_filters=self.get_recording_saving_filters(config),
            required_models=self.get_required_models(config),
            tmp_path=config.paths.tmp_audio,
            cprofile_output=config.paths.cprofile_management,
        )

        self.add_task(
            function=cprofile_management_task,
            schedule=datetime.timedelta(seconds=120),
            queue="celery",
        )

    ## ---------- Get specific conditions for tasks  ---------- ##
    def get_recording_conditions(
        self, config: ProgramConfig
    ) -> List[types.RecordingCondition]:
        """Create the recording conditions for the recording task."""
        timezone = zoneinfo.ZoneInfo(config.timezone)
        return [
            components.IsInIntervals(
                intervals=[
                    data.TimeInterval(
                        start=config.recording.schedule_start,
                        end=datetime.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                    ),
                    data.TimeInterval(
                        start=datetime.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                        end=config.recording.schedule_end,
                    ),
                ],
                timezone=timezone,
            )
        ]

    def get_required_models(self, config: ProgramConfig) -> list[str]:
        name = getattr(self.model, "name", None)
        if name is not None:
            return [name]

        name = getattr(self.model, "__name__", None)
        if name is not None:
            return [name]

        raise ValueError("Model must have a name attribute.")

    def get_output_cleaners(
        self, config: ProgramConfig
    ) -> List[types.ModelOutputCleaner]:
        return []

    def get_processing_filters(
        self, config: ProgramConfig
    ) -> List[types.ProcessingFilter]:
        return []

    def get_message_factories(
        self, config: ProgramConfig
    ) -> List[types.MessageBuilder]:
        return []

    def get_recording_saving_filters(
        self, config: ProgramConfig
    ) -> List[types.RecordingSavingFilter]:
        return []

    def get_recording_saving_managers(
        self, config: ProgramConfig
    ) -> List[types.RecordingSavingManager]:
        return []
