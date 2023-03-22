from datetime import datetime
from uuid import UUID

from pony.orm import Database, Optional, PrimaryKey, Required, Set
from pony.orm.core import EntityMeta

db = Database()

BaseModel: EntityMeta = db.Entity


class Recording(BaseModel):
    """An audio recording entry."""

    id = PrimaryKey(UUID, auto=True)
    path = Required(str)
    duration_s = Required(float)  # duration in seconds
    samplerate_hz = Required(int)
    channels = Required(int)
    datetime = Required(datetime)
    detections = Set("Detection")
    deployment = Required("Deployment")
    recording_messages = Set("RecordingMessage")


class Deployment(BaseModel):
    """A deployment DB entry."""

    id = PrimaryKey(UUID, auto=True)
    site_name = Optional(str)
    latitude = Optional(float)
    longitude = Optional(float)
    recordings = Set(Recording)
    deployment_messages = Set("DeploymentMessage")


class Detection(BaseModel):
    id = PrimaryKey(UUID, auto=True)
    probability = Required(float)
    species_name = Required(str)
    recording = Required(Recording)
    detection_messages = Set("DetectionMessage")


class MessageStatus(BaseModel):
    id = PrimaryKey(int, auto=True)
    response_ok = Required(bool)
    response_code = Required(str)
    sent_on = Required(datetime)
    deployment_message = Optional("DeploymentMessage")
    recording_message = Optional("RecordingMessage")
    detection_message = Optional("DetectionMessage")


class DeploymentMessage(BaseModel):
    id = PrimaryKey(int, auto=True)
    deployment = Required(Deployment)
    message_status = Required(MessageStatus)


class RecordingMessage(BaseModel):
    id = PrimaryKey(int, auto=True)
    recording = Required(Recording)
    message_status = Required(MessageStatus)


class DetectionMessage(BaseModel):
    id = PrimaryKey(int, auto=True)
    detection = Required(Detection)
    message_status = Required(MessageStatus)


db.generate_mapping()
