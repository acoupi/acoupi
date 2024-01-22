"""Acoupi TestProgram Configuraiton Options.

This is the most basic acoupi program. It only records audio files and
does not do any processing and messanging.
"""
import datetime
from pathlib import Path
from typing import Optional

import pytz
from pydantic import BaseModel, Field, model_validator

from acoupi import components, data, tasks
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.programs.base import AcoupiProgram
from acoupi.programs.workers import AcoupiWorker, WorkerConfig

"""Default paramaters for Acoupi TestProgram"""


class AudioConfig(BaseModel):
    """Audio and microphone configuration parameters."""

    audio_duration: int = 5
    """Duration of each audio recording in seconds."""

    recording_interval: int = 10
    """Interval between each audio recording in seconds."""

    # @model_validator(mode="after")
    # def validate_audio_duration(cls, value):
    #     """Validate audio duration."""
    #
    #     if value.audio_duration > value.recording_interval:
    #         raise ValueError(
    #             "Audio duration cannot be greater than recording interval."
    #         )
    #
    #     return value


class RecordingSchedule(BaseModel):
    """Recording schedule config."""

    start_recording: datetime.time = datetime.time(hour=5, minute=30, second=0)

    end_recording: datetime.time = datetime.time(hour=20, minute=0, second=0)


class SaveRecordingFilter(BaseModel):
    """Recording saving options configuration."""

    starttime: datetime.time = datetime.time(hour=21, minute=30, second=0)

    endtime: datetime.time = datetime.time(hour=23, minute=30, second=0)

    before_dawndusk_duration: int = 10

    after_dawndusk_duration: int = 10

    frequency_duration: int = 5

    frequency_interval: int = 5


class ConfigSchema(BaseModel):
    """Configuration Schema for Test Program."""

    dbpath: Path = Path.home() / "storages" / "acoupi.db"

    audio_dir: Path = Path.home() / "storages" / "recordings"

    timeformat: str = "%Y%m%d_%H%M%S"

    timezone: str = "Europe/London"

    microphone_config: MicrophoneConfig

    audio_config: AudioConfig = Field(
        default_factory=AudioConfig,
    )

    recording_schedule: RecordingSchedule = Field(
        default_factory=RecordingSchedule,
    )

    recording_saving: Optional[SaveRecordingFilter] = None


class Program(AcoupiProgram):
    """Test Program."""

    config: ConfigSchema

    worker_config = WorkerConfig(
        workers=[
            AcoupiWorker(
                name="default",
                queues=["celery", "default"],
            ),
            AcoupiWorker(
                name="recording",
                queues=["recording"],
                concurrency=1,
            ),
        ]
    )

    def setup(self, config: ConfigSchema):
        """Setup."""
        self.validate_dirs(config)

        microphone = config.microphone_config
        self.recorder = components.PyAudioRecorder(
            duration=config.audio_config.audio_duration,
            samplerate=microphone.samplerate,
            audio_channels=microphone.audio_channels,
            device_name=microphone.device_name,
        )
        self.store = components.SqliteStore(config.dbpath)
        self.file_manager = components.IDFileManager(config.audio_dir)

        def rename_file(recording: Optional[data.Recording]):
            """Rename the file."""
            if not recording:
                return

            if not recording.path:
                return

            parent_dir = recording.path.parent
            name = recording.path.name
            new_name = parent_dir / f"{name}_processed.wav"
            recording.path.rename(new_name)
            self.store.update_recording_path(recording, new_name)

        recording_task = tasks.generate_recording_task(
            recorder=self.recorder,
            store=self.store,
            logger=self.logger.getChild("recording"),
            recording_conditions=self.create_recording_conditions(config),
        )

        file_management_task = tasks.generate_file_management_task(
            store=self.store,
            logger=self.logger.getChild("file_management"),
            file_manager=self.file_manager,
            file_filters=self.create_file_filters(config),
        )

        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(
                seconds=config.audio_config.recording_interval
            ),
            callbacks=[rename_file],
            queue="recording",
        )

        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=1),
            queue="default",
        )

    def validate_dirs(self, config: ConfigSchema):
        """Validate directories."""
        if not config.audio_dir.exists():
            config.audio_dir.mkdir(parents=True)

        if not config.dbpath.parent.exists():
            config.dbpath.parent.mkdir(parents=True)

    def create_recording_conditions(self, config: ConfigSchema):
        timezone = pytz.timezone(config.timezone)
        return [
            components.IsInIntervals(
                intervals=[
                    data.TimeInterval(
                        start=config.recording_schedule.start_recording,
                        end=datetime.datetime.strptime(
                            "23:59:59", "%H:%M:%S"
                        ).time(),
                    ),
                    data.TimeInterval(
                        start=datetime.datetime.strptime(
                            "00:00:00", "%H:%M:%S"
                        ).time(),
                        end=config.recording_schedule.end_recording,
                    ),
                ],
                timezone=timezone,
            )
        ]

    def create_file_filters(self, config: ConfigSchema):
        if not config.recording_saving:
            # No saving filters defined
            return []

        saving_filters = []
        timezone = pytz.timezone(config.timezone)
        recording_saving = config.recording_saving

        # Main filter
        # Will only save recordings if the recording time is in the
        # interval defined by the start and end time.
        saving_filters.append(
            components.SaveIfInInterval(
                interval=data.TimeInterval(
                    start=recording_saving.starttime,
                    end=recording_saving.endtime,
                ),
                timezone=timezone,
            )
        )

        # Additional filters
        if (
            recording_saving.frequency_duration is not None
            and recording_saving.frequency_interval is not None
        ):
            # This filter will only save recordings at a frequency defined
            # by the duration and interval.
            saving_filters.append(
                components.FrequencySchedule(
                    duration=recording_saving.frequency_duration,
                    frequency=recording_saving.frequency_interval,
                )
            )

        if recording_saving.before_dawndusk_duration is not None:
            # This filter will only save recordings if the recording time
            # is before dawn or dusk.
            saving_filters.append(
                components.Before_DawnDuskTimeInterval(
                    duration=recording_saving.before_dawndusk_duration,
                    timezone=timezone,
                )
            )

        if components.After_DawnDuskTimeInterval is not None:
            # This filter will only save recordings if the recording time
            # is after dawn or dusk.
            saving_filters.append(
                components.After_DawnDuskTimeInterval(
                    duration=recording_saving.after_dawndusk_duration,
                    timezone=timezone,
                )
            )

        return saving_filters
