""" Acoupi TestProgram Configuraiton Options.
    
    This is the most basic acoupi program. It only records audio files
    and does not do any processing and messanging.

    """
import datetime
from pathlib import Path
from typing import Optional

from acoupi import components, data, tasks
from acoupi.programs.base import AcoupiProgram
from pydantic import BaseModel, Field
from acoupi.system.constants import ACOUPI_HOME

"""Default paramaters for Acoupi TestProgram"""


class AudioConfig(BaseModel):
    """Audio and microphone configuration parameters."""

    audio_duration: int = 10

    samplerate: int = 48_000

    audio_channels: int = 1

    chunksize: int = 2048

    device_index: int = 0

    recording_interval: int = 5


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

    frequency_interval: int = 30


class AudioDirectories(BaseModel):
    """Audio Recording Directories configuration."""

    audio_dir_true: Path = Path.home() / "storages" / "recordings"


class AcoupiTest_ConfigSchema(BaseModel):
    """Configuration Schema for Test Program."""

    name: str = "acoupi_testprogram"

    dbpath: Path = ACOUPI_HOME / "storages" / "acoupi.db"

    timeformat: str = "%Y%m%d_%H%M%S"

    timezone: str = "Europe/London"

    audio_config: AudioConfig = Field(
        default_factory=AudioConfig,
    )

    recording_schedule: RecordingSchedule = Field(
        default_factory=RecordingSchedule,
    )

    recording_saving: Optional[SaveRecordingFilter] = Field(
        default_factory=SaveRecordingFilter,
    )

    audio_directories: Optional[AudioDirectories] = Field(
        default_factory=AudioDirectories,
    )


class TestProgram(AcoupiProgram):
    """Test Program."""

    config: AcoupiTest_ConfigSchema

    def setup(self, config: AcoupiTest_ConfigSchema):
        """Setup.

        1. Create Audio Recording Task
        2. Create Detection Task
        3. Create Saving Recording Filter and Management Task
        4. Create Message Task

        """
        dbpath = components.SqliteStore(config.dbpath)

        # Step 1 - Audio Recordings Task
        recording_task = tasks.generate_recording_task(
            recorder=components.PyAudioRecorder(
                duration=config.audio_config.audio_duration,
                samplerate=config.audio_config.samplerate,
                audio_channels=config.audio_config.audio_channels,
                chunksize=config.audio_config.chunksize,
                device_index=config.audio_config.device_index,
            ),
            store=dbpath,
            # logger
            recording_conditions=[
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
                    timezone=config.timezone,
                )
            ],
        )

        # Step 2 - Model Detections Task
        """Detection Task is ignored. No model is provided."""

        # Step 3 - Files Management Task
        def create_file_filters():
            saving_filters = []

            if components.SaveIfInInterval is not None:
                saving_filters.add(
                    components.SaveIfInInterval(
                        interval=data.TimeInterval(
                            start=config.recording_saving.starttime,
                            end=config.recording_saving.endtime,
                        ),
                        timezone=config.timezone,
                    )
                )
            elif components.FrequencySchedule is not None:
                saving_filters.add(
                    components.FrequencySchedule(
                        duration=config.recording_saving.frequency_duration,
                        frequency=config.recording_saving.frequency_interval,
                    )
                )
            elif components.Before_DawnDuskTimeInterval is not None:
                saving_filters.add(
                    components.Before_DawnDuskTimeInterval(
                        duration=config.recording_saving.before_dawndusk_duration,
                        timezone=config.timezone,
                    )
                )
            elif components.After_DawnDuskTimeInterval is not None:
                saving_filters.add(
                    components.After_DawnDuskTimeInterval(
                        duration=config.recording_saving.after_dawndusk_duration,
                        timezone=config.timezone,
                    )
                )
            else:
                raise UserWarning(
                    "No saving filters defined - no files will be saved."
                )

            return saving_filters

        file_management_task = (
            tasks.generate_file_management_task(
                store=dbpath,
                file_manager=components.SaveRecordingManager(
                    dirpath_true=config.audio_directories.audio_dir_true,
                    timeformat=config.timeformat,
                ),
                file_filters=create_file_filters(),
            ),
        )

        # Step 4 - Send Data Task
        """Send Data Task is ignored. No messenger is provided."""

        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(seconds=10),
        )

        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=10),
        )
