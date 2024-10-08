"""Database models for the sqlite store."""

from datetime import datetime
from uuid import UUID

from pony import orm

from .types import BaseModels

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

        name = orm.Required(str)
        """Deployment name."""

        started_on = orm.Required(datetime, unique=True)
        """Datetime when the deployment started. Should be unique."""

        ended_on = orm.Optional(datetime)
        """Datetime when the deployment ended."""

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

        audio_channels = orm.Required(int, default=1)
        """Number of audio_channels in the recording"""

        deployment = orm.Required(Deployment, column="deployment_id")
        """Deployment that the recording belongs to."""

        model_outputs = orm.Set("ModelOutput")
        """Model outputs that belong to the recording."""

    class PredictedTag(BaseModel):
        _table_ = "predicted_tag"

        id = orm.PrimaryKey(int, auto=True)
        """Unique ID of the predicted tag"""

        key = orm.Required(str)
        """Key of the predicted tag"""

        value = orm.Required(str)
        """Value of the predicted tag"""

        confidence_score = orm.Required(float)
        """Score of the predicted tag"""

        detection = orm.Optional("Detection", column="detection_id")

        model_output = orm.Optional("ModelOutput", column="model_output_id")

    class Detection(BaseModel):  # type: ignore
        _table_ = "detection"

        id = orm.PrimaryKey(UUID, auto=True)
        """Unique ID of the detection"""

        location = orm.Optional(str)
        """Location of the detection in the recording"""

        detection_score = orm.Required(float)
        """Score of the detection"""

        tags = orm.Set(PredictedTag)
        """Predicted tags of the detection"""

        model_output = orm.Required("ModelOutput", column="model_output_id")
        """Model output that the detection belongs to."""

    class ModelOutput(BaseModel):
        _table_ = "model_output"

        id = orm.PrimaryKey(UUID, auto=True)
        """Unique ID of the model output."""

        model_name = orm.Required(str)
        """Name of the model that produced the output."""

        recording = orm.Required(Recording, column="recording_id")
        """Recording that the model output belongs to."""

        tags = orm.Set(PredictedTag)
        """Predicted tags of the model output at the file level."""

        detections = orm.Set("Detection")
        """Detections of the model output."""

        created_on = orm.Required(datetime, default=datetime.now)
        """Datetime when the model output was created."""

    return BaseModels(
        Recording=Recording,  # type: ignore
        Deployment=Deployment,  # type: ignore
        PredictedTag=PredictedTag,  # type: ignore
        Detection=Detection,  # type: ignore
        ModelOutput=ModelOutput,  # type: ignore
    )
