"""Test Acoupi Program."""
import datetime
from pathlib import Path

from celery.schedules import crontab
from pydantic import BaseModel, Field

from acoupi import components, data, tasks
from acoupi.components.models.model_test import TestModel
from acoupi.programs.base import AcoupiProgram
from acoupi.system.constants import ACOUPI_HOME

from acoupi.programs.base import AcoupiProgram


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


# class RecordingSaving(BaseModel):
class SaveRecordingFilter(BaseModel):
    """Recording saving options configuration."""

    starttime: datetime.time = datetime.time(hour=21, minute=30, second=0)

    endtime: datetime.time = datetime.time(hour=23, minute=30, second=0)

    before_dawndusk_duration: int = 10

    after_dawndusk_duration: int = 10

    frequency_duration: int = 5

    frequency_interval: int = 30

    threshold: float = 0.8


class AudioDirectories(BaseModel):
    """Audio Recording Directories configuration."""

    audio_dir_true: Path = Path.home() / "storages" / "bats" / "recordings"

    audio_dir_false: Path = Path.home() / "storages" / "no_bats" / "recordings"


class MQTT_MessageConfig(BaseModel):
    """MQTT configuration to send messages."""

    host: str = "localhost"

    port: int = 1884

    client_password: str = "guest"

    client_username: str = "guest"

    topic: str = "mqtt-topic"

    clientid: str = "mqtt-clientid"


class HTTP_MessageConfig(BaseModel):
    """MQTT configuration to send messages."""

    deviceid: str = "device-id"

    baseurl: str = "base-url"

    client_password: str = "guest"

    client_id: str = "guest"

    api_key: str = "guest"

    content_type: str = "application-json"


class TestConfigSchema(BaseModel):
    """Configuration Schema for Test Program."""

    name: str = "test_program"

    threshold: float = 0.2

    dbpath: Path = ACOUPI_HOME / "storages" / "acoupi.db"

    timeformat: str = "%Y%m%d_%H%M%S"

    timezone: str = "Europe/London"

    audio_config: AudioConfig = Field(default_factory=AudioConfig)

    recording_schedule: RecordingSchedule = Field(
        default_factory=RecordingSchedule
    )

    recording_saving: SaveRecordingFilter = Field(
        default_factory=SaveRecordingFilter
    )

    audio_directories: AudioDirectories = Field(
        default_factory=AudioDirectories
    )

    mqtt_message_config: MQTT_MessageConfig = Field(
        default_factory=MQTT_MessageConfig
    )
    http_message_config: HTTP_MessageConfig = Field(
        default_factory=HTTP_MessageConfig
    )


class TestProgram(AcoupiProgram):
    """Test Program."""

    config: TestConfigSchema

    def setup(self, config: TestConfigSchema):
        """Setup Test Program."""
        print("Setting up test program")

        def test_task():
            """Simple task."""
            print(f"Configuration: name={config.name}")
            print("Task executed")

        # Schedule the task to run every 10 seconds
        self.add_task(test_task, schedule=10)
