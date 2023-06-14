"""Types for acoupi ORM models."""

from datetime import datetime
from typing import List, NamedTuple, Optional
from uuid import UUID

from pony.orm import Json, core

__all__ = [
    "BaseModels",
    "Deployment",
    "PredictedTag",
    "Recording",
    "Detection",
    "ModelOutput",
]


class Deployment(core.EntityMeta):
    """Deployment ORM model."""

    id: UUID
    """Unique ID of the deployment."""

    name: str
    """Deployment name"""

    started_on: datetime
    """Datetime when the deployment started. Should be unique."""

    latitude: Optional[float]
    """Latitude of the deployment site. Can be None if unknown."""

    longitude: Optional[float]
    """Longitude of the deployment site. Can be None if unknown."""


class Recording(core.EntityMeta):
    """Recording ORM model."""

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

    channels: int
    """Number of channels in the recording"""

    deployment: Deployment
    """Deployment that the recording belongs to"""

    model_outputs: List["ModelOutput"]
    """Model outputs that belong to the recording"""


class PredictedTag(core.EntityMeta):
    """Predicted tag ORM model."""

    id: int
    """Unique ID of the predicted tag"""

    key: str
    """Key of the predicted tag"""

    value: str
    """Value of the predicted tag"""

    probability: float
    """Probability of the predicted tag"""

    detection: Optional["Detection"]
    """Detection that the predicted tag belongs to"""

    model_output: Optional["ModelOutput"]
    """Model output that the predicted tag belongs to"""


class Detection(core.EntityMeta):
    """Detection ORM model."""

    id: UUID
    """Unique ID of the detection."""

    location: Json
    """Location of the detection."""

    probability: float
    """Probability of the detection."""

    tags: List[PredictedTag]
    """Predicted tags of the detection."""

    model_output: "ModelOutput"
    """Model output that the detection belongs to."""


class ModelOutput(core.EntityMeta):
    """Model output ORM model."""

    id: UUID
    """Unique ID of the model output"""

    model_name: str
    """Name of the model"""

    recording: Recording
    """Recording that the model output belongs to"""

    tags: List[PredictedTag]
    """Predicted tags of the model output at the file level"""

    detections: List[Detection]
    """Detections of the model output"""

    created_on: datetime
    """Datetime when the model output was created"""


class BaseModels(NamedTuple):
    """Container for models."""

    Deployment: Deployment
    Recording: Recording
    PredictedTag: PredictedTag
    Detection: Detection
    ModelOutput: ModelOutput
