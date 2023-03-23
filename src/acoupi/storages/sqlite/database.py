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
        """A deployment DB entry."""

        _table_ = "deployment"

        id = PrimaryKey(UUID, auto=True)
        site_name = Optional(str)
        latitude = Optional(float)
        longitude = Optional(float)
        recordings = Set("Recording")
        deployment_messages = Set("DeploymentMessage")

    class Recording(BaseModel):  # type: ignore
        """An audio recording entry."""

        _table_ = "recording"

        id = PrimaryKey(UUID, auto=True)
        path = Required(str)
        duration_s = Required(float)
        samplerate_hz = Required(int)
        channels = Required(int)
        datetime = Required(datetime)
        deployment = Required(Deployment, column="deployment_id")
        detections = Set("Detection")
        recording_messages = Set("RecordingMessage")

    class Detection(BaseModel):  # type: ignore
        _table_ = "detection"

        id = PrimaryKey(UUID, auto=True)
        probability = Required(float)
        species_name = Required(str)
        recording = Required(Recording, column="recording_id")
        detection_messages = Set("DetectionMessage")

    class MessageStatus(BaseModel):  # type: ignore
        _table_ = "message_status"

        id = PrimaryKey(int, auto=True)
        response_ok = Required(bool)
        response_code = Required(str)
        sent_on = Required(datetime)
        deployment_message = Optional("DeploymentMessage")
        recording_message = Optional("RecordingMessage")
        detection_message = Optional("DetectionMessage")

    class DeploymentMessage(BaseModel):  # type: ignore
        _table_ = "deployment_message"

        id = PrimaryKey(int, auto=True)
        deployment = Required(Deployment, column="deployment_id")
        message_status = Required(MessageStatus, column="message_status_id")

    class RecordingMessage(BaseModel):  # type: ignore
        _table_ = "recording_message"

        id = PrimaryKey(int, auto=True)
        recording = Required(Recording, column="recording_id")
        message_status = Required(MessageStatus, column="message_status_id")

    class DetectionMessage(BaseModel):  # type: ignore
        _table_ = "detection_message"

        id = PrimaryKey(int, auto=True)
        detection = Required(Detection, column="detection_id")
        message_status = Required(MessageStatus, column="message_status_id")

    return database, Models(
        Recording=Recording,
        Deployment=Deployment,
        Detection=Detection,
        MessageStatus=MessageStatus,
        DeploymentMessage=DeploymentMessage,
        RecordingMessage=RecordingMessage,
        DetectionMessage=DetectionMessage,
    )
