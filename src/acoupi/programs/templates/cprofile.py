"""CProfile Program template module."""

import datetime
import zoneinfo
from pathlib import Path
from typing import Annotated, Callable, Optional, TypeVar

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

__all__ = []


class AudioConfiguration(BaseModel):
    """Audio configuration schema."""

    duration: int = 3
    """Duration of each audio recording in seconds."""

    interval: int = 12
    """Interval between each audio recording in seconds."""

    chunksize: Annotated[int, NoUserPrompt] = 8192
    """Chunksize of audio recording."""

    schedule_start: datetime.time = Field(
        default=datetime.time(hour=6, minute=0, second=0),
    )
    """Start time for recording schedule."""

    schedule_end: datetime.time = Field(
        default=datetime.time(hour=22, minute=30, second=0),
    )
    """End time for recording schedule."""


class PathsConfiguration(BaseModel):
    """Data configuration schema."""

    tmp_audio: Path = Field(default_factory=get_temp_dir)
    """Temporary directory for storing audio files."""

    recordings: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "recordings",
    )
    """Directory for storing audio files permanently."""

    db_metadata: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "metadata.db",
    )
    """Path to the metadata database."""

    cprofile_management: Path = Field(
        default_factory=lambda: Path.home() / "cprofile_management.prof",
    )
    """Path for the cprofile output of the tasks."""


class BasicProgramConfiguration(BaseModel):
    """Configuration schema for a basic program."""

    timezone: TimeZoneName = Field(default=TimeZoneName("Europe/London"))
    """Time zone where the device will be deployed."""

    microphone: MicrophoneConfig
    """Microphone configuration."""

    recording: AudioConfiguration = Field(default_factory=AudioConfiguration)
    """Audio configuration."""

    paths: PathsConfiguration = Field(default_factory=PathsConfiguration)
    """Data configuration."""


ProgramConfig = TypeVar("ProgramConfig", bound=BasicProgramConfiguration)


class CProfile_BasicProgram(AcoupiProgram[ProgramConfig]):
    """Basic Acoupi Program."""

    worker_config = DEFAULT_WORKER_CONFIG

    recorder: types.AudioRecorder

    store: types.Store

    def setup(self, config: ProgramConfig) -> None:
        """Set up the basic program.

        This method initialises the program's components (audio recorder,
        store, and file manager), registers the recording and file management
        tasks, and performs necessary setup operations.
        """
        self.validate_dirs(config)
        self.recorder = self.configure_recorder(config)
        self.store = self.configure_store(config)
        self.register_recording_task(config)
        self.register_file_management_task(config)
        super().setup(config)

    def on_start(self, deployment: data.Deployment):
        """Handle program start event.

        This method is called when the program starts and stores the
        deployment information in the metadata store.
        """
        self.store.store_deployment(deployment)
        super().on_start(deployment)

    def on_end(self, deployment: data.Deployment) -> None:
        """Handle program end event.

        This method is called when the program ends and updates the
        deployment information in the metadata store.
        """
        self.store.update_deployment(deployment)
        super().on_end(deployment)

    def check(self, config: ProgramConfig):
        """Check the program's components.

        This method performs checks on the program's components to ensure
        they are functioning correctly. Currently, it only checks the PyAudio
        recorder if it is being used.
        """
        recorder_check = getattr(self.recorder, "check", None)
        if callable(recorder_check):
            recorder_check()

        super().check(config)

    def configure_recorder(
        self,
        config: ProgramConfig,
    ) -> types.AudioRecorder:
        """Configure the audio recorder."""
        microphone = config.microphone
        return components.PyAudioRecorder(
            duration=config.recording.duration,
            samplerate=microphone.samplerate,
            audio_channels=microphone.audio_channels,
            device_name=microphone.device_name,
            chunksize=config.recording.chunksize,
            audio_dir=config.paths.tmp_audio,
        )

    def configure_store(
        self,
        config: ProgramConfig,
    ) -> types.Store:
        """Configure the metadata store."""
        return components.SqliteStore(config.paths.db_metadata)

    def get_file_managers(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingSavingManager]:
        """Get the file managers."""
        return [components.DateFileManager(config.paths.recordings)]

    def get_audio_recording_conditions(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingCondition]:
        """Get the recording conditions."""
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

    def get_recordings_saving_filters(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingSavingFilter]:
        """Get the recording saving filters."""
        return []

    def get_recording_callbacks(
        self,
        config: ProgramConfig,
    ) -> list[Callable[[Optional[data.Recording]], None]]:
        """Get the recording callbacks."""
        return []

    def get_required_models(self, config: ProgramConfig) -> list[str]:
        """Get the required models."""
        return []

    ### --- Task Creation --- ###
    def create_recording_task(
        self,
        config: ProgramConfig,
    ) -> Callable[[], Optional[data.Recording]]:
        """Create the recording task."""
        return tasks.generate_recording_task(
            recorder=self.recorder,
            store=self.store,
            logger=self.logger.getChild("recording"),
            recording_conditions=self.get_audio_recording_conditions(config),
        )

    def create_file_management_task(
        self,
        config: ProgramConfig,
    ) -> Callable[[], None]:
        """Create the file management task."""
        return tasks.generate_cprofile_management_task(
            store=self.store,
            logger=self.logger.getChild("file_management"),
            file_managers=self.get_file_managers(config),
            file_filters=self.get_recordings_saving_filters(config),
            required_models=self.get_required_models(config),
            cprofile_path=config.paths.cprofile_management,
            tmp_path=config.paths.tmp_audio,
        )

    ### --- Task Registration to Celery Workers --- ###
    def register_recording_task(
        self,
        config: ProgramConfig,
    ) -> None:
        """Register the recording task."""
        recording_task = self.create_recording_task(config)
        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(seconds=config.recording.interval),
            callbacks=self.get_recording_callbacks(config),
            queue="recording",
        )

    def register_file_management_task(
        self,
        config: ProgramConfig,
    ) -> None:
        """Register the file management task."""
        file_management_task = self.create_file_management_task(config)
        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=2),
            queue="celery",
        )

    def validate_dirs(self, config: ProgramConfig):
        """Validate the directories used by the program.

        This method ensures that the necessary directories for storing audio
        and metadata exist. If they don't, it creates them.
        """
        if not config.paths.tmp_audio.exists():
            config.paths.tmp_audio.mkdir(parents=True)

        if not config.paths.recordings.exists():
            config.paths.recordings.mkdir(parents=True)

        if not config.paths.db_metadata.parent.exists():
            config.paths.db_metadata.parent.mkdir(parents=True)

        if not config.paths.cprofile_management.parent.exists():
            config.paths.cprofile_management.parent.mkdir(parents=True)
