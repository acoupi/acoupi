"""Batdetect2 Program."""
import datetime
from pathlib import Path

from celery.schedules import crontab
from pydantic import BaseModel, Field

from acoupi import components, data, tasks
from acoupi.programs.base import AcoupiProgram

"""Default paramaters for Batdetect2 Program"""


class AudioConfig(BaseModel):
    """Audio and microphone configuration parameters."""

    audio_duration: int = 3

    samplerate: int = 192_000

    audio_channels: int = 1

    chunksize: int = 8192

    device_index: int = 0

    recording_interval: int = 10


class RecordingSchedule(BaseModel):
    """Recording schedule config."""

    start_recording: datetime.time = datetime.time(hour=12, minute=0, second=0)

    end_recording: datetime.time = datetime.time(hour=21, minute=0, second=0)


class RecordingSaving(BaseModel):
    """Recording saving options configuration."""

    starttime_saving_recording: datetime.time = datetime.time(
        hour=21, minute=30, second=0
    )

    endtime_saving_recording: datetime.time = datetime.time(
        hour=23, minute=30, second=0
    )

    before_dawndusk_duration: int = 10

    after_dawndusk_duration: int = 10

    saving_frequency_duration: int = 5

    saving_frequency_interval: int = 30


class AudioDirectories(BaseModel):
    """Audio Recording Directories configuration."""

    audio_dir_true: Path = Path.home() / "storages" / "bats" / "recordings"

    audio_dir_false: Path = Path.home() / "storages" / "no_bats" / "recordings"


class MessageConfig(BaseModel):
    """MQTT configuration to send messages."""

    host: str = "localhost"

    port: int = 1884

    client_password: str = "guest"

    client_username: str = "guest"

    topic: str = "mqtt-topic"

    clientid: str = "mqtt-clientid"


class BatDetect2_ConfigSchema(BaseModel):
    """BatDetect2 Configuration Schematic."""

    name: str = "batdetect2"

    threshold: float = 0.2

    dbpath: Path = Path.home() / "storages" / "acoupi.db"

    timeformat: str = "%Y%m%d_%H%M%S"

    timezone: str = "Europe/London"

    audio_config: AudioConfig = Field(default_factory=AudioConfig)

    recording_schedule: RecordingSchedule = Field(
        default_factory=RecordingSchedule
    )

    recording_saving: RecordingSaving = Field(default_factory=RecordingSaving)

    audio_directories: AudioDirectories = Field(
        default_factory=AudioDirectories
    )

    message_config: MessageConfig = Field(default_factory=MessageConfig)


class BatDetect2_Program(AcoupiProgram):
    """BatDetect2 Program."""

    config: BatDetect2_ConfigSchema

    def setup(self, config: BatDetect2_ConfigSchema):
        """Setup.

        1. Create Audio Recording Task
        2. Create Detection Task
        3. Create Saving Recording Management Task
        4. Create Message Task

        """
        dbpath = components.SqliteStore(config.dbpath)
        dbpath_message = components.SqliteMessageStore(db_path=config.dbpath)

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
        detection_task = tasks.generate_detection_task(
            store=dbpath,
            model=components.BatDetect2(),
            message_store=dbpath_message,
            # logger
            output_cleaners=[
                components.ThresholdDetectionFilter(threshold=config.threshold)
            ],
            message_factories=[components.FullModelOutputMessageBuilder()],
        )

        # Step 3 - Files Management Task
        file_management_task = tasks.generate_file_management_task(
            store=dbpath,
            file_manager=components.SaveRecording(
                dirpath_true=config.audio_directories.audio_dir_true,
                dirpath_false=config.audio_directories.audio_dir_false,
                timeformat=config.timeformat,
                threshold=config.threshold,
            ),
            file_filters=[
                components.Before_DawnDuskTimeInterval(
                    duration=config.recording_saving.before_dawndusk_duration,
                    timezone=config.timezone,
                ),
                components.After_DawnDuskTimeInterval(
                    duration=config.recording_saving.after_dawndusk_duration,
                    timezone=config.timezone,
                ),
            ],
        )

        # Step 4 - Send Data Task
        send_data_task = tasks.generate_send_data_task(
            message_store=dbpath_message,
            messenger=components.MQTTMessenger(
                host=config.message_config.host,
                port=config.message_config.port,
                password=config.message_config.client_password,
                username=config.message_config.client_username,
                topic=config.message_config.topic,
                clientid=config.message_config.clientid,
            ),
        )

        self.add_task(
            function=recording_task,
            callbacks=[detection_task],
            schedule=datetime.timedelta(seconds=10),
        )

        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=10),
        )

        # TODO: Add task send_data, file_management.

        self.add_task(
            function=send_data_task,
            schedule=crontab(minute="*/1"),
        )
