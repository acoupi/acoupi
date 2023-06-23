from pydantic import BaseModel, Field
from typing import Optional

from acoupi.config_schemas import BaseConfigSchema
from acoupi.programs.base import AcoupiProgram


class AudioConfig(BaseModel):
    """Audio and microphone configuration parameters."""

    samplerate: int = DEFAULT_SAMPLERATE
    audio_channels: int = DEFAULT_AUDIOCHANNELS
    chunksize: int = DEFAULT_CHUNKSIZE
    duration: int = DEFAULT_DURATION
    recording_interval: int = DEFAULT_INTERVAL


class RecordingSchedule(BaseModel):
    """Recording schedule config."""

    start_recording: datetime.time = START_RECORDING_TIME
    end_recording: datetime.time = END_RECORDING_TIME


class RecordingSaving(BaseModel):
    """Recording saving options configuration."""

    starttime_saving_recording: Optional[datetime.time] = START_SAVING_RECORDING
    endtime_saving_recording: Optional[datetime.time] = END_SAVING_RECORDING
    timeafter_dawndusk: Optional[int] = AFTER_DAWNDUSK_DURATION 
    timeafter_sunset: Optional[int] = BEFORE_DAWNDUSK_DURATION
    saving_frequency_duration: Optional[int] = SAVE_FREQUENCY_DURATION
    saving_frequency_interval: Optional[int] = SAVE_FREQUENCY_INTERVAL


class MessageConfig(BaseModel):
    "MQTT configuration to send messages"

    host: str = DEFAULT_MQTT_HOST
    port: int = DEFAULT_MQTT_PORT
    client_username: Optional[str] = DEFAULT_MQTT_CLIENT_USER
    client_password: Optional[str] = DEFAULT_MQTT_CLIENT_PASS
    topic: Optional[str] = DEFAULT_MQTT_TOPIC
    clientid: Optional[str] = DEFAULT_MQTT_CLIENTID


class BatDetect2ConfigSchema(BaseConfigSchema):
    """BatDetect2 Configuration Schematic"""

    name: str = "batdetect2"
    
    audio_config: AudioConfig = Field(default_factory=AudioConfig)
    recording_schedule: RecordingSchedule = Field(default_factory=RecordingSchedule)
    recording_saving: RecordingSaving = Field(default_factory=RecordingSaving)
    message_config = Field(default_factory=MessageConfig)


    @classmethod
    def add_arguments(cls, parser):
        """Define arugments.""" 
        parser.add_arguments(
            "--latitude",
            type=float,
            default=LATITUDE,
        )
        parser.add_arguments(
            "--longitude",
            type=float,
            default=LONGITUDE,
        )
        parser.add_arguments(
            "--timezone",
            type=str, 
            default=DEFAULT_TIMEZONE,
        )
        parser.add_arguments(
            "--samplerate", 
            type=int, 
            default=DEFAULT_SAMPLERATE,
        )
        parser.add_arguments(
            "--audio_channels",
            type=int, 
            default=DEFAULT_AUDIOCHANNELS
        )
        parser.add_arguments(
            "--chunksize", 
            type=int, 
            default=DEFAULT_CHUNKSIZE,
        )
        parser.add_arguments(
            "--duration",
            type=int, 
            default=DEFAULT_DURATION
        )