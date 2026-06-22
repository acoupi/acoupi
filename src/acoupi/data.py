"""Data objects for acoupi System."""

import datetime
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import (
    Any,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

__all__ = [
    "AwareDatetime",
    "TimeInterval",
    "Deployment",
    "Recording",
    "PredictedTag",
    "PredictionType",
    "Detection",
    "PresenceDetection",
    "SequenceDetection",
    "EventDetection",
    "ModelOutput",
    "ModelOutputInfo",
    "Message",
    "ResponseStatus",
    "Response",
    "BoundingBox",
]


def utc_now() -> AwareDatetime:
    return datetime.datetime.now(datetime.timezone.utc)


class TimeInterval(BaseModel):
    """An interval of time between two times of day."""

    start: datetime.time
    """Start time of the interval."""

    end: datetime.time
    """End time of the interval."""


class DeviceInfo(BaseModel):
    """Runtime information about the current device.

    This object is intentionally small and currently only exposes the device
    identifier used in filename templates and heartbeat-style messages.
    """

    id: str
    """Unique identifier for the current device, if available."""


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

    started_on: AwareDatetime = Field(default_factory=utc_now)
    """The datetime when the device was deployed."""

    ended_on: Optional[AwareDatetime] = None
    """The datetime when the deployment ended."""

    @field_validator("started_on", "ended_on", mode="before")
    def add_missing_timezone(cls, v):
        if isinstance(v, str):
            # Leave timezone-aware strings to Pydantic so parsing remains
            # consistent across Python versions, especially for trailing ``Z``.
            if v.endswith("Z") or "+" in v[10:] or "-" in v[10:]:
                return v

            v = datetime.datetime.fromisoformat(v)

        if isinstance(v, datetime.datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=datetime.timezone.utc)

        return v

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

    created_on: AwareDatetime = Field(default_factory=utc_now, repr=False)
    """The datetime when the recording was made"""

    duration: float = Field(
        repr=False,
    )
    """The duration of the recording in seconds"""

    samplerate: int = Field(repr=False)
    """The samplerate of the recording in Hz"""

    deployment: Deployment = Field(repr=False)
    """The deployment that the recording belongs to"""

    path: Optional[Path] = Field(None, repr=True)
    """The path to the audio file in the local filesystem"""

    audio_channels: Optional[int] = Field(default=1, repr=False)
    """The number of audio_channels in the recording."""

    time_expansion: float = Field(default=1, repr=False, gt=0)
    """Factor by which the recording's time scale is multiplied.

    Values > 1.0 indicate time expansion (slowing down playback), while values
    between 0.0 and 1.0 indicate time compression (speeding up playback).
    """

    id: UUID = Field(default_factory=uuid4, repr=True)
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


@dataclass(slots=True, frozen=True)
class Tag:
    """A Tag is a label for a recording."""

    key: str
    """The key of the tag."""

    value: str
    """The value of the tag."""


@dataclass(slots=True, frozen=True)
class PredictedTag:
    """A PredictedTag is a label predicted by a model.

    It consists of a key, a value and a score.
    """

    tag: Tag
    """The tag predicted by the model."""

    confidence_score: float = 1
    """The confidence score of the predicted tag."""


class BoundingBox(BaseModel):
    """BoundingBox to locate a sound event in time and frequency.

    All time values are in seconds and all frequency values are in Hz.
    """

    model_config = ConfigDict(frozen=True)

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


class PredictionType(str, Enum):
    """Describe what kind of sound pattern a detection refers to.

    This helps explain how to interpret the area covered by a detection.
    A detection may refer to a general presence of sound in a region, one
    whole sequence of related sounds, or one single sound event.
    """

    PRESENCE = "presence"
    """One or more target sounds are present in the detected region."""

    SEQUENCE = "sequence"
    """Exactly one sequence of related sounds is present in the detected region."""

    EVENT = "event"
    """Exactly one single target sound event is present in the detected region."""


class Detection(BaseModel):
    """A Detection is a single prediction from a model.

    The ``prediction_type`` explains what kind of thing the detection refers
    to. In most cases, it is easier to use one of the convenience classes
    instead of setting this field manually:

    - ``PresenceDetection`` for one or more target sounds in a region.
    - ``SequenceDetection`` for exactly one sequence of related sounds.
    - ``EventDetection`` for exactly one single sound event.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the detection"""

    prediction_type: "PredictionType"
    """The semantic type of prediction represented by this detection."""

    location: Optional[BoundingBox] = None
    """The location of the detection in the recording."""

    detection_score: float = 1
    """The score of the detection."""

    tags: List[PredictedTag] = Field(default_factory=list)
    """The tags predicted by the model for the detection."""

    @field_validator("detection_score")
    def validate_score(cls, value):
        """Validate that the score is between 0 and 1."""
        if value < 0 or value > 1:
            raise ValueError("score must be between 0 and 1")
        return value

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.prediction_type,
                self.location,
                self.detection_score,
                tuple(sorted(hash(t) for t in self.tags)),
            )
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Detection):
            return NotImplemented

        # Check standard fields first by creating a dict copy without the list fields
        self_dict = self.model_dump(exclude={"tags"})
        other_dict = other.model_dump(exclude={"tags"})

        if self_dict != other_dict:
            return False

        self_tags = set(self.tags)
        other_tags = set(other.tags)
        return self_tags == other_tags


class PresenceDetection(Detection):
    """Detection for a region where one or more target sounds are present.

    This is the most general detection type. It is useful for full-recording,
    clip-level, or bounding-box predictions when the detected region may
    contain one or more sound events.
    """

    prediction_type: "PredictionType" = Field(
        default=PredictionType.PRESENCE,
        init=False,
        repr=False,
    )


class SequenceDetection(Detection):
    """Detection for a region that contains exactly one sequence of sounds.

    Use this when the detected region refers to one meaningful group of
    related sounds rather than a single event.
    """

    prediction_type: "PredictionType" = Field(
        default=PredictionType.SEQUENCE,
        init=False,
        repr=False,
    )


class EventDetection(Detection):
    """Detection for a region that contains exactly one target sound event.

    Use this when the detected region is intended to describe one single
    sound event.
    """

    prediction_type: "PredictionType" = Field(
        default=PredictionType.EVENT,
        init=False,
        repr=False,
    )


class ModelOutput(BaseModel):
    """The output of a model."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the model output."""

    name_model: str
    """The name of the model that produced the output."""

    recording: Recording
    """The recording that was used as input to the model."""

    detections: Sequence[Detection] = Field(default_factory=list)
    """List of predicted sound events in the recording."""

    created_on: AwareDatetime = Field(default_factory=utc_now)
    """The datetime when the model output was created."""

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ModelOutput):
            return NotImplemented

        # Check standard fields first by creating a dict copy without the list fields
        self_dict = self.model_dump(exclude={"detections"})
        other_dict = other.model_dump(exclude={"detections"})

        if self_dict != other_dict:
            return False

        self_detections = set(d for d in self.detections)
        other_detections = set(d for d in other.detections)
        return self_detections == other_detections


class ModelOutputInfo(BaseModel):
    """Lightweight model-output information for management-style queries."""

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the model output."""

    name_model: str
    """The name of the model that produced the output."""

    created_on: AwareDatetime = Field(default_factory=utc_now)
    """The datetime when the model output was created."""


class Message(BaseModel):
    """The message to be sent to the remote server."""

    id: UUID = Field(default_factory=uuid4)
    """The unique ID of the message."""

    content: Union[str, bytes]
    """The message to be sent. Usually JSON text, but may be raw bytes."""

    created_on: AwareDatetime = Field(default_factory=utc_now)
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

    received_on: AwareDatetime = Field(default_factory=utc_now)
    """The datetime the message was received."""


class Metric(BaseModel):
    """A metric is a single value with a name and unit.

    Used to report the status of a system or model.
    """

    name: str
    """The name of the metric."""

    value: float
    """The value of the metric."""

    captured_on: datetime.datetime = Field(default_factory=utc_now)
    """The date and time the metric was captured."""

    unit: str
    """The unit of the metric."""
