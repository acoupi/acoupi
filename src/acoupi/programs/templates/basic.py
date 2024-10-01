"""Basic Program template module.

This module provides a template for creating a basic Acoupi program.

The template includes:

- **BasicProgramMixin:** A mixin class that provides a basic program
  implementation with features for audio recording, metadata storage, and
  file management.
- **Configuration Schema:**  Defines the configuration schema
  (`BasicConfiguration`) required to configure a basic program, including
  settings for audio recording, data storage, and microphone configuration.

A basic program, utilizing this template, performs the following tasks:

- Records audio at regular intervals.
- Manages audio files on disk (e.g., saving recordings permanently).

Key Components:

- **Audio Recorder:**  Records audio clips according to the specified
    configuration.
- **Metadata Store:** Stores metadata associated with recordings.
- **File Manager:**  Handles saving audio recordings to persistent storage.

To use this template, create a new program class that inherits from
`BasicProgramMixin` and configure it using the `BasicConfiguration` schema.
"""

import datetime
import zoneinfo
from pathlib import Path
from typing import Annotated, Callable, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic_extra_types.timezone_name import TimeZoneName

from acoupi import components, data, tasks
from acoupi.components import types
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.data import TimeInterval
from acoupi.programs import (
    AcoupiWorker,
    NoUserPrompt,
    WorkerConfig,
)
from acoupi.programs.core.base import ProgramProtocol
from acoupi.system.files import get_temp_dir

__all__ = []


class AudioConfiguration(BaseModel):
    """Audio configuration schema."""

    duration: int = 3
    """Duration of each audio recording in seconds."""

    interval: int = 5
    """Interval between each audio recording in seconds."""

    chunksize: Annotated[int, NoUserPrompt] = 8192
    """Chunksize of audio recording."""

    schedule: List[TimeInterval] = Field(
        default_factory=lambda: [
            TimeInterval(start=datetime.time.min, end=datetime.time.max)
        ]
    )
    """Schedule for recording audio."""


class DataConfiguration(BaseModel):
    """Data configuration schema."""

    tmp: Path = Field(default_factory=get_temp_dir)
    """Temporary directory for storing audio files."""

    audio: Path = Field(default_factory=lambda: Path.home() / "audio")
    """Directory for storing audio files permanently."""

    metadata: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "metadata.db",
    )
    """Path to the metadata database."""


class BasicConfiguration(BaseModel):
    """Configuration schema for a basic program."""

    timezone: TimeZoneName = Field(default=TimeZoneName("Europe/London"))
    """Time zone where the device will be deployed."""

    microphone: MicrophoneConfig
    """Microphone configuration."""

    audio: AudioConfiguration = Field(default_factory=AudioConfiguration)
    """Audio configuration."""

    data: DataConfiguration = Field(default_factory=DataConfiguration)
    """Data configuration."""


ProgramConfig = TypeVar("ProgramConfig", bound=BasicConfiguration)


class BasicProgramMixin(ProgramProtocol[ProgramConfig]):
    """Basic program mixin.

    This mixin provides a basic program implementation with the following
    components:

    - **Audio Recorder:** Records audio clips according to the program's
    configuration.
    - **File Manager:** Manages the storage of audio recordings, including
    saving them to permanent storage.
    - **Store:**  Provides an interface for storing and retrieving metadata
    associated with the program and its recordings.

    Tasks:

    The mixin includes the following pre-defined tasks:

    - **Audio Recording:**  Records audio at regular intervals, configurable
      through the `audio` settings in the `BasicConfiguration` schema.
    - **File Management:**  Periodically performs file management operations,
    such as moving recordings from temporary to permanent storage.

    Customization:

    Customize the program's behavior by inheriting from this mixin and
    overriding these methods:

    - `get_recording_conditions`:  Modify the conditions that trigger audio
    recording.
    - `get_recording_filters`:  Add filters to determine which recordings to
    save.
    - `get_recording_callbacks`: Define actions to perform after a recording is
    made.

    Examples
    --------
    Creating a basic program with custom recording conditions:


    ```python
    import datetime
    from acoupi import components, data
    from acoupi.programs import AcoupiProgram
    from acoupi.programs.templates import (
        BasicProgramMixin,
        BasicConfiguration,
    )


    class Config(BasicConfiguration):
        pass


    class Program(BasicProgramMixin, AcoupiProgram):
        configuration_schema = Config

        def get_recording_conditions(self, config: Config):
            # Get the default recording conditions
            conditions = super().get_recording_conditions(
                config
            )

            return [
                components.IsInInterval(
                    data.TimeInterval(
                        start=datetime.time(hour=3),
                        end=datetime.time(hour=6),
                    )
                ),
                *conditions,
            ]
    ```
    """

    worker_config: Optional[WorkerConfig] = WorkerConfig(
        workers=[
            AcoupiWorker(
                name="recording",
                queues=["recording"],
                concurrency=1,
            ),
            AcoupiWorker(
                name="default",
                queues=["celery"],
            ),
        ],
    )

    recorder: types.AudioRecorder

    store: types.Store

    file_manager: types.RecordingSavingManager

    def setup(self, config: ProgramConfig) -> None:
        """Set up the basic program.

        This method initializes the program's components (audio recorder,
        store, and file manager), registers the recording and file management
        tasks, and performs necessary setup operations.
        """
        self.validate_dirs(config)
        self.recorder = self.configure_recorder(config)
        self.store = self.configure_store(config)
        self.file_manager = self.configure_file_manager(config)
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
        if isinstance(self.recorder, components.PyAudioRecorder):
            self.recorder.check()
        super().check(config)

    def configure_recorder(
        self,
        config: ProgramConfig,
    ) -> types.AudioRecorder:
        """Configure the audio recorder.

        This method creates and configures an instance of the `PyAudioRecorder`
        based on the provided configuration.

        Returns
        -------
        types.AudioRecorder
            The configured audio recorder instance.
        """
        microphone = config.microphone
        return components.PyAudioRecorder(
            duration=config.audio.duration,
            samplerate=microphone.samplerate,
            audio_channels=microphone.audio_channels,
            device_name=microphone.device_name,
            chunksize=config.audio.chunksize,
            audio_dir=config.data.tmp,
        )

    def configure_store(
        self,
        config: ProgramConfig,
    ) -> types.Store:
        """Configure the metadata store.

        This method creates and configures an instance of the `SqliteStore`
        based on the provided configuration.

        Returns
        -------
        types.Store
            The configured metadata store instance.
        """
        return components.SqliteStore(config.data.metadata)

    def configure_file_manager(
        self,
        config: ProgramConfig,
    ) -> types.RecordingSavingManager:
        """Configure the file manager.

        This method creates and configures an instance of the `DateFileManager`
        based on the provided configuration.

        Returns
        -------
        types.RecordingSavingManager
            The configured file manager instance.
        """
        return components.DateFileManager(config.data.audio)

    def get_recording_conditions(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingCondition]:
        """Get the recording conditions.

        This method defines the conditions under which audio recording should
        be performed. By default, it uses the schedule defined in the
        configuration.

        Returns
        -------
        list[types.RecordingCondition]
            A list of recording conditions.
        """
        return [
            components.IsInIntervals(
                intervals=config.audio.schedule,
                timezone=zoneinfo.ZoneInfo(config.timezone),
            )
        ]

    def get_recording_filters(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingSavingFilter]:
        """Get the recording saving filters.

        This method defines filters that determine which recordings should be
        saved permanently. By default, it returns an empty list, meaning all
        recordings are saved.

        Returns
        -------
        list[types.RecordingSavingFilter]
            A list of recording saving filters.
        """
        return []

    def get_recording_callbacks(
        self,
        config: ProgramConfig,
    ) -> list[Callable[[Optional[data.Recording]], None]]:
        """Get the recording callbacks.

        This method defines callbacks to be executed after a recording is
        completed. By default, it returns an empty list.

        Returns
        -------
        list[Callable[[Optional[data.Recording]], None]]
            A list of recording callbacks.
        """
        return []

    def create_recording_task(
        self,
        config: ProgramConfig,
    ) -> Callable[[], Optional[data.Recording]]:
        """Create the recording task.

        This method creates the task responsible for recording audio.

        Returns
        -------
        Callable[[], Optional[data.Recording]]
            The recording task.
        """
        recording_conditions = self.get_recording_conditions(config)
        return tasks.generate_recording_task(
            recorder=self.recorder,
            store=self.store,
            logger=self.logger.getChild("recording"),
            recording_conditions=recording_conditions,
        )

    def create_file_management_task(
        self,
        config: ProgramConfig,
    ) -> Callable[[], None]:
        """Create the file management task.

        This method creates the task responsible for managing audio files.

        Returns
        -------
        Callable[[], None]
            The file management task.
        """
        file_filters = self.get_recording_filters(config)
        return tasks.generate_file_management_task(
            store=self.store,
            logger=self.logger.getChild("file_management"),
            file_managers=[self.file_manager],
            file_filters=file_filters,
            tmp_path=config.data.tmp,
        )

    def register_recording_task(
        self,
        config: ProgramConfig,
    ) -> None:
        """Register the recording task.

        This method registers the recording task with the program's scheduler.
        """
        recording_task = self.create_recording_task(config)
        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(seconds=config.audio.interval),
            callbacks=self.get_recording_callbacks(config),
            queue="recording",
        )

    def register_file_management_task(
        self,
        config: ProgramConfig,
    ) -> None:
        """Register the file management task.

        This method registers the file management task with the program's
        scheduler.
        """
        file_management_task = self.create_file_management_task(config)
        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=1),
            queue="celery",
        )

    def validate_dirs(self, config: ProgramConfig):
        """Validate the directories used by the program.

        This method ensures that the necessary directories for storing audio
        and metadata exist. If they don't, it creates them.
        """
        if not config.data.tmp.exists():
            config.data.tmp.mkdir(parents=True)

        if not config.data.audio.exists():
            config.data.audio.mkdir(parents=True)

        if not config.data.metadata.parent.exists():
            config.data.metadata.parent.mkdir(parents=True)
