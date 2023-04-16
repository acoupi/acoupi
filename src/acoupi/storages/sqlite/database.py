"""Database models for the acoupi database."""
from datetime import datetime
from uuid import UUID

from pony import orm

from acoupi.storages.sqlite.types import BaseModels, MessageModels

__all__ = [
    "create_base_models",
]


def create_base_models(database: orm.Database) -> BaseModels:
    """Create the database and return the database and models."""
    BaseModel = database.Entity

    class Deployment(BaseModel):  # type: ignore
        _table_ = "deployment"

        id = orm.PrimaryKey(UUID, auto=True)
        """Unique ID of the deployment."""

        device_id = orm.Required(str)
        """Device ID."""

        name = orm.Required(str)
        """Deployment name."""

        started_on = orm.Required(datetime, unique=True)
        """Datetime when the deployment started. Should be unique."""

        latitude = orm.Optional(float)
        """Latitude of the deployment site. Can be None if unknown."""

        longitude = orm.Optional(float)
        """Longitude of the deployment site. Can be None if unknown."""

        recordings = orm.Set("Recording")
        """Recordings that belong to the deployment."""

    class Recording(BaseModel):  # type: ignore
        _table_ = "recording"

        id = orm.PrimaryKey(UUID, auto=True)
        """Unique ID of the recording."""

        path = orm.Optional(str, unique=True)
        """Path to the recording file. 

        Can be None if the recording is not stored locally."""

        datetime = orm.Required(datetime, unique=True)
        """Datetime of the recording. Should be unique."""

        duration_s = orm.Required(float)
        """Duration of the recording in seconds."""

        samplerate_hz = orm.Required(int)
        """Samplerate of the recording in Hz"""

        channels = orm.Required(int, default=1)
        """Number of channels in the recording"""

        deployment = orm.Required(Deployment, column="deployment_id")
        """Deployment that the recording belongs to."""

        detections = orm.Set("Detection")
        """Detections that were made on the recording."""

    class Detection(BaseModel):  # type: ignore
        _table_ = "detection"

        id = orm.PrimaryKey(UUID, auto=True)
        """Unique ID of the detection"""

        probability = orm.Required(float)
        """Probability of the detection"""

        species_name = orm.Required(str)
        """Name of the species that was detected"""

        recording = orm.Required(Recording, column="recording_id")
        """Recording that the detection belongs to"""

    return BaseModels(
        Recording=Recording,  # type: ignore
        Deployment=Deployment,  # type: ignore
        Detection=Detection,  # type: ignore
    )


def create_message_models(
    database: orm.Database,
) -> MessageModels:
    BaseModel = database.Entity

    class MessageStatus(BaseModel):  # type: ignore
        _table_ = "message_status"

        id = orm.PrimaryKey(int, auto=True)
        """Unique ID of the message status"""

        response_ok = orm.Required(bool)
        """Whether the response was received successfully"""

        response_code = orm.Required(str)
        """Response code of the response"""

        sent_on = orm.Required(datetime)
        """Datetime when the message was sent"""

        deployment_message = orm.Optional("DeploymentMessage")
        recording_message = orm.Optional("RecordingMessage")
        detection_message = orm.Optional("DetectionMessage")

    class DeploymentMessage(BaseModel):  # type: ignore
        _table_ = "deployment_message"

        id = orm.PrimaryKey(int, auto=True)
        """Unique ID of the deployment message"""

        deployment_id = orm.Required(UUID, column="deployment_id")
        """Deployment that the message belongs to"""

        message_status = orm.Required(
            MessageStatus, column="message_status_id"
        )
        """Message status of the message"""

    class RecordingMessage(BaseModel):  # type: ignore
        _table_ = "recording_message"

        id = orm.PrimaryKey(int, auto=True)
        """Unique ID of the recording message"""

        recording_id = orm.Required(UUID, column="recording_id")
        """Recording that the message belongs to"""

        message_status = orm.Required(
            MessageStatus,
            column="message_status_id",
        )
        """Message status of the message"""

    class DetectionMessage(BaseModel):  # type: ignore
        _table_ = "detection_message"

        id = orm.PrimaryKey(int, auto=True)
        """Unique ID of the detection message"""

        detection_id = orm.Required(UUID, column="detection_id")
        """Detection that the message belongs to"""

        message_status = orm.Required(
            MessageStatus,
            column="message_status_id",
        )
        """Message status of the message"""

    return MessageModels(
        MessageStatus=MessageStatus,  # type: ignore
        DeploymentMessage=DeploymentMessage,  # type: ignore
        RecordingMessage=RecordingMessage,  # type: ignore
        DetectionMessage=DetectionMessage,  # type: ignore
    )
