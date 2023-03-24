"""Types for acoupi ORM models."""

from datetime import datetime
from typing import List, NamedTuple, Optional
from uuid import UUID

from pony.orm.core import EntityMeta

__all__ = [
    "Models",
]


class Deployment(EntityMeta):
    id: UUID
    """Unique ID of the deployment."""

    device_id: str
    """Device ID of the deployment."""

    started_on: datetime
    """Datetime when the deployment started. Should be unique."""

    latitude: Optional[float]
    """Latitude of the deployment site. Can be None if unknown."""

    longitude: Optional[float]
    """Longitude of the deployment site. Can be None if unknown."""

    recordings = List["Recording"]
    """Recordings that belong to the deployment."""

    deployment_messages = List["DeploymentMessage"]
    """Messages that were sent about the deployment."""


class Recording(EntityMeta):
    id: UUID
    """Unique ID of the recording"""

    path: Optional[str]
    """Path to the recording file. Can be None if the recording is not stored locally"""

    datetime: datetime
    """Datetime of the recording. Should be unique"""

    duration_s: float
    """Duration of the recording in seconds"""

    samplerate_hz: int
    """Samplerate of the recording in Hz"""

    deployment: Deployment
    """Deployment that the recording belongs to"""

    detections: List["Detection"]
    """Detections that were made on the recording"""

    recording_messages: List["RecordingMessage"]
    """Messages that were sent about the recording"""


class Detection(EntityMeta):
    id: UUID
    """Unique ID of the detection"""

    probability: float
    """Probability of the detection"""

    species_name: str
    """Name of the species that was detected"""

    recording: Recording
    """Recording that the detection belongs to"""

    detection_messages: List["DetectionMessage"]
    """Messages that were sent about the detection"""


class MessageStatus(EntityMeta):
    id: int
    """Unique ID of the message status"""

    response_ok: bool
    """Whether the response was received successfully"""

    response_code: str
    """Response code of the response"""

    sent_on: datetime
    """Datetime when the message was sent"""

    deployment_message: Optional["DeploymentMessage"]
    recording_message: Optional["RecordingMessage"]
    detection_message: Optional["DetectionMessage"]


class DeploymentMessage(EntityMeta):
    id: int
    """Unique ID of the deployment message"""

    deployment: Deployment
    """Deployment that the message belongs to"""

    message_status: MessageStatus
    """Message status of the message"""


class RecordingMessage(EntityMeta):
    id: int
    """Unique ID of the recording message"""

    recording: Recording
    """Recording that the message belongs to"""

    message_status: MessageStatus
    """Message status of the message"""


class DetectionMessage(EntityMeta):
    id: int
    """Unique ID of the detection message"""

    detection: Detection
    """Detection that the message belongs to"""

    message_status: MessageStatus
    """Message status of the message"""


class Models(NamedTuple):
    """Container for all ORM models."""

    Deployment: Deployment
    Recording: Recording
    Detection: Detection
    MessageStatus: MessageStatus
    DeploymentMessage: DeploymentMessage
    RecordingMessage: RecordingMessage
    DetectionMessage: DetectionMessage
