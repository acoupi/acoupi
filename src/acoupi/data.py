"""Data objects for acoupi System."""
import datetime
from enum import IntEnum
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator, field_validator

__all__ = [
    "TimeInterval",
    "Deployment",
    "Recording",
    "PredictedTag",
    "Detection",
    "ModelOutput",
    "Message",
    "ResponseStatus",
    "Response",
    "BoundingBox",
]


class TimeInterval(BaseModel):
    """An interval of time between two times of day."""

    start: datetime.time
    """Start time of the interval."""

    end: datetime.time
    """End time of the interval."""

    @model_validator(mode="before")
    def validate_interval(cls, values):
        """Validate that the start time is before the end time."""
        if values["start"] >= values["end"]:
            raise ValueError("start time must be before end time")
        return values


class Deployment(BaseModel):
    """A Deployment captures information about the device deployment.

    This includes the latitude, longitude, and deployment start.
    """

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the deployment."""

    name: str
    """User provided name of the deployment."""

    latitude: Optional[float] = None
    """The latitude of the site where the device is deployed."""

    longitude: Optional[float] = None
    """The longitude of the site where the device is deployed."""

    started_on: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    """The datetime when the device was deployed."""

    @field_validator("latitude")
    def validate_latitude(cls, value):
        """Validate that the latitude are within range."""
        if value is not None and (value < -90 or value > 90):
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    def validate_longitude(cls, value):
        """Validate that the longitude are within range."""
        if value is not None and (value < -180 or value > 180):
            raise ValueError("longitude must be between -180 and 180")
        return value


class Recording(BaseModel):
    """A Recording is a single audio file recorded from the microphone."""

    datetime: datetime.datetime
    """The datetime when the recording was made"""

    duration: float
    """The duration of the recording in seconds"""

    samplerate: int
    """The samplerate of the recording in Hz"""

    deployment: Deployment
    """The deployment that the recording belongs to"""

    path: Optional[Path] = None
    """The path to the audio file in the local filesystem"""

    audio_channels: int = 1
    """The number of audio_channels in the recording. Defaults to 1."""

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the recording"""

    @field_validator("duration")
    def validate_duration(cls, value):
        """Validate that the duration is greater than 0."""
        if value <= 0:
            raise ValueError("duration must be greater than 0")
        return value

    @field_validator("samplerate")
    def validate_samplerate(cls, value):
        """Validate that the samplerate is greater than 0."""
        if value <= 0:
            raise ValueError("samplerate must be greater than 0")
        return value

    @field_validator("audio_channels")
    def validate_audio_channels(cls, value):
        """Validate that the number of audio_channels is greater than 1."""
        if value <= 0:
            raise ValueError("audio_channels must be 1 or greater")
        return value


class Tag(BaseModel):
    """A Tag is a label for a recording."""

    key: str
    """The key of the tag."""

    value: str
    """The value of the tag."""

    @field_validator("key")
    def validate_key(cls, value):
        """Validate that the key is not empty."""
        if not value:
            raise ValueError("key cannot be empty")
        return value

    @field_validator("value")
    def validate_value(cls, value):
        """Validate that the value is not empty."""
        if not value:
            raise ValueError("value cannot be empty")
        return value


class PredictedTag(BaseModel):
    """A PredictedTag is a label predicted by a model.

    It consists of a key, a value and a probability.
    """

    tag: Tag
    """The tag predicted by the model."""

    probability: float = 1
    """The probability of the tag prediction."""

    @field_validator("probability")
    def validate_probability(cls, value):
        """Validate that the probability is between 0 and 1."""
        if value < 0 or value > 1:
            raise ValueError("probability must be between 0 and 1")
        return value


class BoundingBox(BaseModel):
    """BoundingBox to locate a sound event in time and frequency.

    All time values are in seconds and all frequency values are in Hz.
    """

    type: str = "BoundingBox"

    coordinates: Tuple[float, float, float, float]

    @classmethod
    def from_coordinates(
        cls,
        start_time: float,
        low_freq: float,
        end_time: float,
        high_freq: float,
    ):
        """Create a BoundingBox from coordinates."""
        return cls(
            coordinates=(start_time, low_freq, end_time, high_freq),
        )

    @field_validator("coordinates")
    def validate_coordinates(cls, value):
        """Validate that the coordinates are within range."""
        start_time, low_freq, end_time, high_freq = value

        if end_time <= start_time:
            raise ValueError("end time must be greater than start time")

        if low_freq >= high_freq:
            raise ValueError(
                "high frequency must be greater than low frequency"
            )

        return value


class Detection(BaseModel):
    """A Detection is a single prediction from a model."""

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the detection"""

    location: Optional[BoundingBox] = None
    """The location of the detection in the recording."""

    probability: float = 1
    """The probability of the detection."""

    tags: List[PredictedTag] = Field(default_factory=list)
    """The tags predicted by the model for the detection."""

    @field_validator("probability")
    def validate_probability(cls, value):
        """Validate that the probability is between 0 and 1."""
        if value < 0 or value > 1:
            raise ValueError("probability must be between 0 and 1")
        return value

    @field_validator("tags")
    def sort_tags(cls, value):
        """Sort tags."""
        return sorted(
            value,
            key=lambda x: (x.probability, x.tag.key, x.tag.value),
            reverse=True,
        )


class ModelOutput(BaseModel):
    """The output of a model."""

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the model output."""

    name_model: str
    """The name of the model that produced the output."""

    recording: Recording
    """The recording that was used as input to the model."""

    tags: List[PredictedTag] = Field(default_factory=list)
    """The tags predicted by the model at the recording level."""

    detections: List[Detection] = Field(default_factory=list)
    """List of predicted sound events in the recording."""

    created_on: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    """The datetime when the model output was created."""

    @field_validator("tags")
    def sort_tags(cls, value):
        """Sort tags."""
        return sorted(
            value,
            key=lambda x: (x.probability, x.tag.key, x.tag.value),
            reverse=True,
        )

    @field_validator("detections")
    def sort_detections(cls, value):
        """Sort detections by ID."""
        return sorted(
            value,
            key=lambda x: x.id,
        )


class Message(BaseModel):
    """The message to be sent to the remote server."""

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the message."""

    content: str
    """The message to be sent. Usually a JSON string."""

    created_on: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    """The datetime when the message was created."""


class ResponseStatus(IntEnum):
    """The status of a message."""

    SUCCESS = 0
    """The message was received successfully."""

    FAILED = 1
    """The message failed to send."""

    ERROR = 2
    """The message was sent, but there was an error."""

    TIMEOUT = 3
    """The message timed out."""


class Response(BaseModel):
    """The response from sending a message."""

    status: ResponseStatus
    """The status of the message."""

    message: Message
    """The message that was sent."""

    content: Optional[str] = None
    """The content of the response."""

    received_on: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    """The datetime the message was received."""
