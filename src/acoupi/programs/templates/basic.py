"""Basic Program template module.

This module provides a base class (`BasicProgram`) for creating basic Acoupi
programs. It offers essential features for audio recording, metadata storage,
and file management.

The `BasicProgram` class defines the following components:

- **Audio Recorder:**  Records audio clips according to the program's
  configuration.
- **Store:** Provides an interface for storing and retrieving metadata
  associated with the program and its recordings.

Using these components, `BasicProgram` creates and manages the following
tasks:

- **Audio Recording:** Records audio at regular intervals, configurable
  through the `audio` settings in the `BasicProgramConfiguration` schema.
- **File Management:**  Periodically performs file management operations,
  such as moving recordings from temporary to permanent storage.

Configuration:

The program's configuration is defined by the `BasicProgramConfiguration`
schema, which includes settings for:

- Timezone
- Microphone configuration
- Audio recording settings (duration, interval, schedule)
- Data storage locations (temporary directory, audio directory,
  metadata database)

Usage:

To create a basic Acoupi program, define a new class that inherits from
`BasicProgram`.

Customization:

You can customise the program's behavior by overriding the following methods:

- `get_recording_conditions`:  Modify the conditions that trigger audio
  recording.
- `get_recording_filters`:  Add filters to determine which recordings to
  save permanently.
- `get_recording_callbacks`: Define actions to perform after a recording
  is made.

"""

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
from acoupi.system.tasks import get_task_list, run_task

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


class BasicProgram(AcoupiProgram[ProgramConfig]):
    """Basic Acoupi Program.

    This class provides a base for creating basic Acoupi programs. It offers
    essential features for audio recording, metadata storage, and file
    management.

    Components:

    - **Audio Recorder:** Records audio clips according to the program's
      configuration.
    - **Store:** Provides an interface for storing and retrieving metadata
      associated with the program and its recordings.

    Tasks:

    Using the components above, this class creates and manages the following
    tasks:

    - **Audio Recording:** Records audio at regular intervals, configurable
      through the `audio` settings in the `BasicProgramConfiguration` schema.
    - **File Management:** Periodically performs file management operations,
      such as moving recordings from temporary to permanent storage.

    Customization:

    customise the program's behavior by overriding these methods:

    - `get_recording_conditions`: Define the specific conditions that must be
        met for audio recording to continue when the recording task is
        triggered by the scheduler.
    - `get_recording_filters`:  Add filters to determine which recordings to
      save.
    - `get_recording_callbacks`: Define actions to perform after a recording
      is made.

    Examples
    --------
    ```python
    import datetime
    from acoupi import components, data
    from acoupi.programs.templates import (
        BasicProgram,
        BasicProgramConfiguration,
    )


    class Config(BasicProgramConfiguration):
        pass


    class Program(BasicProgram):
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

        This method is called when the program ends. It updates the
        deployment information in the metadata store, and ensure that
        remaining tasks are completed before the program is stopped.

        Tasks to check are:
        - file_management_task (if implemented). Check if there are remaining
        files in the temporary directory and move them to the correct directory.
        """
        self.store.update_deployment(deployment)
        super().on_end(deployment)

        tmp_audio_path = self.config.paths.tmp_audio
        tmp_files = list(tmp_audio_path.glob("*"))

        if len(tmp_files) > 0:
            print(
                f"Running file_management_task to manage {len(tmp_files)}"
                " remaining files in the temporary directory."
            )
            self.tasks["file_management_task"].apply()
            run_task(self, "file_management_task")

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
        """Configure the metadata store.

        This method creates and configures an instance of the `SqliteStore`
        based on the provided configuration.

        Returns
        -------
        types.Store
            The configured metadata store instance.
        """
        return components.SqliteStore(config.paths.db_metadata)

    def get_file_managers(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingSavingManager]:
        """Get the file managers.

        This method defines how audio recordings should be saved and managed.
        It returns a list of file managers that are responsible for determining
        the final storage location of each recording.

        When a recording is marked for saving, the program iterates through the
        list of file managers in order. Each manager can either:

        - Return a path where the recording should be saved.
        - Return `None` to indicate that it cannot handle the recording,
        allowing the next manager in the list to be used.

        By default, this method returns a list containing a single
        `DateFileManager`, which saves recordings in a structured folder
        hierarchy based on the recording date.

        Returns
        -------
        list[types.RecordingSavingManager]
            A list of file manager instances.
        """
        return [components.DateFileManager(config.paths.recordings)]

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
        types.RecordingCondition
            A recording condition.
        """
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

    def get_required_models(self, config: ProgramConfig) -> list[str]:
        """Get the required models for a recording to be considered ready.

        This method specifies which bioacoustic models must process a recording
        before it is considered "ready" to be moved from temporary storage.

        By default, no models are required, meaning recordings are immediately
        considered ready. However, you can override this method to define
        specific models that must process the recordings based on the program's
        configuration.

        Returns
        -------
        list[str]
            A list of model names that are required to process a recording
            before it is considered ready.
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
        return tasks.generate_recording_task(
            recorder=self.recorder,
            store=self.store,
            logger=self.logger.getChild("recording"),
            recording_conditions=self.get_recording_conditions(config),
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
        return tasks.generate_file_management_task(
            store=self.store,
            logger=self.logger.getChild("file_management"),
            file_managers=self.get_file_managers(config),
            file_filters=self.get_recording_filters(config),
            required_models=self.get_required_models(config),
            tmp_path=config.paths.tmp_audio,
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
            schedule=datetime.timedelta(seconds=config.recording.interval),
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
