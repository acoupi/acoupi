"""Batdetect2 Program."""
import datetime
from pathlib import Path

from celery.schedules import crontab
from pydantic import BaseModel, Field

from acoupi import components, data
from acoupi.config_schemas import BaseConfigSchema
from acoupi.programs.base import AcoupiProgram
from acoupi.tasks import templates

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


class BatDetect2_ConfigSchema(BaseConfigSchema):
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

    @classmethod
    def add_arguments(cls, parser):
        pass

    #    """Define arugments."""
    #    parser.add_arguments(
    #        "--latitude",
    #        type=float,
    #        default=LATITUDE,
    #    )
    #    parser.add_arguments(
    #        "--longitude",
    #        type=float,
    #        default=LONGITUDE,
    #    )
    #    parser.add_arguments(
    #        "--timezone",
    #        type=str,
    #        default=DEFAULT_TIMEZONE,
    #    )
    #    """ Microphone Configuration Arguments"""
    #    parser.add_arguments(
    #        "--samplerate",
    #        type=int,
    #        default=DEFAULT_SAMPLERATE,
    #    )
    #    parser.add_arguments(
    #        "--audio_channels",
    #        type=int,
    #        default=DEFAULT_AUDIO_CHANNELS
    #    )
    #    parser.add_arguments(
    #        "--chunksize",
    #        type=int,
    #        default=DEFAULT_CHUNKSIZE,
    #    )
    #    parser.add_arguments(
    #        "--device_index",
    #        type=int,
    #        default=DEVICE_INDEX,
    #    )
    #    """ Audio Recordings Configuration Arguments"""
    #    parser.add_arguments(
    #        "--audio_duration",
    #        type=int,
    #        default=DEFAULT_DURATION
    #    )
    #    parser.add_arguments(
    #        "--audio_interval",
    #        type=int,
    #        default=DEFAULT_INTERVAL
    #    )
    #    parser.add_arguments(
    #        "--starttime",
    #        type=datetime.time.fromisoformat,
    #        default=START_RECORDING_TIME
    #    )
    #    parser.add_arguments(
    #        "--endtime",
    #        type=datetime.time.fromisoformat,
    #        default=END_RECORDING_TIME
    #   )
    #    parser.add_arguments(
    #        "--threshold",
    #        type=float,
    #        default=DEFAULT_THRESHOLD,
    #    )
    #    arser.add_arguments(
    #        "--dbpath",
    #        type=float,
    #        default=DEFAULT_DB_PATH,
    #    )
    #    ## TODO: Add Saving Recording Agruments
    #    """Saving Recording Configuration Arguments"""
    #    parser.add_arguments(
    #        "--before_dawndusk",
    #        type=str,
    #        default=BEFORE_DAWNDUSK_DURATION
    #    )
    #    parser.add_arguments(
    #        "--after_dawndusk",
    #        type=str,
    #        default=AFTER_DAWNDUSK_DURATION
    #    )
    #    parser.add_arguments(
    #        "--audiodir_true",
    #        type=Path,
    #        default=DIR_RECORDING_TRUE
    #    )
    #    parser.add_arguments(
    #        "--audiodir_false",
    #        type=Path,
    #        default=DIR_RECORDING_FALSE
    #    )
    #    parser.add_arguments(
    #        "--timeformat",
    #        type=Path,
    #        default=DEFAULT_TIMEFORMAT
    #    )
    #    """ MQTT Configuration Arguments"""
    #    parser.add_arguments(
    #        "--host",
    #        type=str,
    #        default=DEFAULT_MQTT_HOST
    #    )
    #    parser.add_arguments(
    #        "--port",
    #        type=int,
    #        default=DEFAULT_MQTT_PORT
    #    )
    #    parser.add_arguments(
    #        "--client_password",
    #        type=str,
    #        default=DEFAULT_MQTT_CLIENT_PASS
    #    )
    #    parser.add_arguments(
    #        "--client_username",
    #        type=int,
    #        default=DEFAULT_MQTT_CLIENT_USER
    #    )
    #    parser.add_arguments(
    #        "--topic",
    #        type=str,
    #        default=DEFAULT_MQTT_TOPIC
    #    )
    #    parser.add_arguments(
    #        "--clientid",
    #        type=int,
    #        default=DEFAULT_MQTT_CLIENTID
    #    )

    @classmethod
    def from_parsed_args(cls, args):
        """Create config from arguments."""
        return cls()

    #    return cls(
    #        audio_config=AudioConfig(
    #            duration=args.audio_duration,
    #            samplerate=args.samplerate,
    #            audio_channels=args.audio_channels,
    #            chunksize=args.chunksize,
    #            device_index=args.device_index,
    #            interval=args.audio_interval,
    #        ),
    #        recording_schedule=RecordingSchedule(
    #            start_time=args.starttime,
    #            end_time=args.endtime,
    #        ),
    #        recording_saving=RecordingSaving(
    #            before_dawndusk_duration=args.before_dawndusk,
    #            eafter_dawndusk_duration=args.after_dawndusk,
    #        ),
    #        audio_directories=AudioDirectories(
    #            audiodir_true=args.audiodir_true,
    #            audiodir_false=args.audiodir_false,
    #        ),
    #        message_config=MessageConfig(
    #            host=args.host,
    #            port=args.port,
    #            client_password=args.client_password,
    #            client_username=args.client_username,
    #            topic=args.topic,
    #            clientid=args.clientid,
    #        ),
    #        timezone=args.timezone,
    #        timeformat=args.timeformat,
    #        threshold=args.threshold,
    #        dbpath=args.dbpath,
    #    )


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
        recording_task = templates.generate_recording_task(
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
        detection_task = templates.generate_detection_task(
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
        file_management_task = templates.generate_file_management_task(
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
        send_data_task = templates.generate_send_data_task(
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
