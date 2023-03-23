"""Database models for the acoupi database."""

from collections import namedtuple
from datetime import datetime
from typing import Tuple
from uuid import UUID

from pony.orm import Database, Optional, PrimaryKey, Required, Set

__all__ = [
    "create_database",
    "Models",
]

Models = namedtuple(
    "Models",
    [
        "Recording",
        "Deployment",
        "Detection",
        "MessageStatus",
        "DeploymentMessage",
        "RecordingMessage",
        "DetectionMessage",
    ],
)


def create_database() -> Tuple[Database, Models]:
    """Create the database and return the database and models."""

    database = Database()

    BaseModel = database.Entity

    class Deployment(BaseModel):  # type: ignore
        _table_ = "deployment"

        id = PrimaryKey(UUID, auto=True)
        """Unique ID of the deployment."""

        device_id = Required(str)
        """Device ID of the deployment."""

        latitude = Optional(float)
        """Latitude of the deployment site. Can be None if unknown."""

        longitude = Optional(float)
        """Longitude of the deployment site. Can be None if unknown."""

        recordings = Set("Recording")
        """Recordings that belong to the deployment."""

        deployment_messages = Set("DeploymentMessage")
        """Messages that were sent about the deployment."""

    class Recording(BaseModel):  # type: ignore
        _table_ = "recording"

        id = PrimaryKey(UUID, auto=True)
        """Unique ID of the recording"""

        path = Optional(str, unique=True)
        """Path to the recording file. Can be None if the recording is not stored locally"""

        datetime = Required(datetime, unique=True)
        """Datetime of the recording. Should be unique"""

        duration_s = Required(float)
        """Duration of the recording in seconds"""

        samplerate_hz = Required(int)
        """Samplerate of the recording in Hz"""

        channels = Required(int)
        """Number of channels in the recording"""

        deployment = Required(Deployment, column="deployment_id")
        """Deployment that the recording belongs to"""

        detections = Set("Detection")
        """Detections that were made on the recording"""

        recording_messages = Set("RecordingMessage")
        """Messages that were sent about the recording"""

    class Detection(BaseModel):  # type: ignore
        _table_ = "detection"

        id = PrimaryKey(UUID, auto=True)
        """Unique ID of the detection"""

        probability = Required(float)
        """Probability of the detection"""

        species_name = Required(str)
        """Name of the species that was detected"""

        recording = Required(Recording, column="recording_id")
        """Recording that the detection belongs to"""

        detection_messages = Set("DetectionMessage")
        """Messages that were sent about the detection"""

    class MessageStatus(BaseModel):  # type: ignore
        _table_ = "message_status"

        id = PrimaryKey(int, auto=True)
        """Unique ID of the message status"""

        response_ok = Required(bool)
        """Whether the response was received successfully"""

        response_code = Required(str)
        """Response code of the response"""

        sent_on = Required(datetime)
        """Datetime when the message was sent"""

        deployment_message = Optional("DeploymentMessage")
        recording_message = Optional("RecordingMessage")
        detection_message = Optional("DetectionMessage")

    class DeploymentMessage(BaseModel):  # type: ignore
        _table_ = "deployment_message"

        id = PrimaryKey(int, auto=True)
        """Unique ID of the deployment message"""

        deployment = Required(Deployment, column="deployment_id")
        """Deployment that the message belongs to"""

        message_status = Required(MessageStatus, column="message_status_id")
        """Message status of the message"""

    class RecordingMessage(BaseModel):  # type: ignore
        _table_ = "recording_message"

        id = PrimaryKey(int, auto=True)
        """Unique ID of the recording message"""

        recording = Required(Recording, column="recording_id")
        """Recording that the message belongs to"""

        message_status = Required(MessageStatus, column="message_status_id")
        """Message status of the message"""

    class DetectionMessage(BaseModel):  # type: ignore
        _table_ = "detection_message"

        id = PrimaryKey(int, auto=True)
        """Unique ID of the detection message"""

        detection = Required(Detection, column="detection_id")
        """Detection that the message belongs to"""

        message_status = Required(MessageStatus, column="message_status_id")
        """Message status of the message"""

    return database, Models(
        Recording=Recording,
        Deployment=Deployment,
        Detection=Detection,
        MessageStatus=MessageStatus,
        DeploymentMessage=DeploymentMessage,
        RecordingMessage=RecordingMessage,
        DetectionMessage=DetectionMessage,
    )
