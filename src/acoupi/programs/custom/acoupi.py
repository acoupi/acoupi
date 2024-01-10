"""Acoupi TestProgram Configuraiton Options.

This is the most basic acoupi program. It only records audio files and
does not do any processing and messanging.
"""
import datetime
from pathlib import Path
from typing import Optional

import pytz
from pydantic import BaseModel, Field

from acoupi import components, data, tasks
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.programs.base import AcoupiProgram
from acoupi.system.constants import ACOUPI_HOME

"""Default paramaters for Acoupi TestProgram"""


class AudioConfig(BaseModel):
    """Audio and microphone configuration parameters."""

    microphone_config: MicrophoneConfig = Field(
        default_factory=MicrophoneConfig,
    )

    audio_duration: int = 10

    chunksize: int = 2048

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

    frequency_interval: int = 5


class AudioDirectories(BaseModel):
    """Audio Recording Directories configuration."""

    audio_dir: Path = ACOUPI_HOME / "storages" / "recordings"

    audio_dir_true: Optional[Path] = None

    audio_dir_false: Optional[Path] = None


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

    audio_directories: AudioDirectories = Field(
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
        # Get Timezone
        timezone = pytz.timezone(config.timezone)

        microphone = config.audio_config.microphone_config

        # Step 1 - Audio Recordings Task
        recording_task = tasks.generate_recording_task(
            recorder=components.PyAudioRecorder(
                duration=config.audio_config.audio_duration,
                samplerate=microphone.samplerate,
                audio_channels=microphone.audio_channels,
                chunksize=config.audio_config.chunksize,
                device_index=microphone.device_index,
            ),
            store=components.SqliteStore(config.dbpath),
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
                    timezone=timezone,
                )
            ],
        )

        # Step 2 - Model Detections Task
        # Detection Task is ignored. No model is provided.

        # Step 3 - Files Management Task
        def create_file_filters():
            saving_filters = []

            if not config.recording_saving:
                # No saving filters defined
                return []

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

        file_management_task = tasks.generate_file_management_task(
            store=components.SqliteStore(config.dbpath),
            file_manager=components.SaveRecordingManager(
                dirpath=config.audio_directories.audio_dir,
                timeformat=config.timeformat,
            ),
            file_filters=create_file_filters(),
        )

        # Step 4 - Send Data Task
        """Send Data Task is ignored. No messenger is provided."""

        # Final Step - Add Tasks to Program
        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(seconds=10),
        )

        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=10),
        )
