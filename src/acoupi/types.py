"""This module contains the types used by the aucupi."""
import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class Deployment:
    """A Deployment captures information about the device deployment.

    This includes the latitude, longitude, and deployment start.
    """

    started_on: datetime.datetime
    """The datetime when the device was deployed."""

    device_id: str
    """The ID of the device."""

    device_name: str
    """User provided name of the device."""

    latitude: Optional[float] = None
    """The latitude of the site where the device is deployed."""

    longitude: Optional[float] = None
    """The longitude of the site where the device is deployed."""

    deployment_id: UUID = field(default_factory=uuid4)
    """The unique ID of the deployment."""


@dataclass
class Recording:
    """A Recording is a single audio file recorded from the microphone."""

    path: str
    """The path to the audio file in the local filesystem"""

    datetime: datetime.datetime
    """The datetime when the recording was made"""

    duration: float
    """The duration of the recording in seconds"""

    samplerate: int
    """The samplerate of the recording in Hz"""

    recording_id: UUID = field(default_factory=uuid4)
    """The unique ID of the recording"""


@dataclass
class Detection:
    """A Detection is a single prediction from a model."""

    species_name: str
    """The name of the species predicted by the model"""

    probability: float
    """The probability of the prediction"""

    detection_id: UUID = field(default_factory=uuid4)
    """The unique ID of the detection"""


class ScheduleManager(ABC):
    """Manage time between recordings.

    The ScheduleManager is responsible for determining the interval between
    recordings.
    """

    @abstractmethod
    def time_until_next_recording(self) -> int:
        """Return the number of seconds until the next recording.

        This should return 0 if a recording should be made immediately.
        """


class RecordManager(ABC):
    """Decide if a recording should be made.

    The RecordManager is responsible for deciding if a recording
    should be made.
    """

    @abstractmethod
    def should_record(self, time: datetime.datetime) -> bool:
        """Determine if a recording should be made."""


class AudioRecorder(ABC):
    """Record audio from the microphone.

    The AudioRecorder is responsible for recording audio from the
    microphone.
    """

    @abstractmethod
    def record(self) -> Recording:
        """Record audio from the microphone and return the recording.

        The recording should be saved to a temporary file and the path
        to the file should be returned, along with the datetime, duration,
        and samplerate of the recording.

        Other metadata, such as the device_id, lat, and lon, can be
        optionally returned.
        """


class ProcessingFilter(ABC):
    """Determine if a recording should be processed by the model.

    The ProcessingFilter is responsible for determining if a recording
    should be processed by the model.
    """

    @abstractmethod
    def should_process_recording(self, recording: Recording) -> bool:
        """Determine if the recording should be processed by the model."""


class Model(ABC):
    """Model for making predictions.

    The Model is responsible for running the model on the audio file
    and returning the predicted detections.

    Detections should be returned as a list of Detection objects.
    """

    @abstractmethod
    def run(
        self,
        recording: Recording,
        deployment: Optional[Deployment] = None,
    ) -> List[Detection]:
        """Run the model on the audio file and return the result.

        Can optionally use deployment info to enhance predictions.
        """


class DetectorFilter(ABC):
    """Determine if a detection should be saved.

    The DetectorFilter is responsible for determining if a detection
    should be saved.
    """

    @abstractmethod
    def should_store_detection(self, detection: Detection) -> bool:
        """Determine if the detection should be stored locally."""


class Store(ABC):
    """The Store is responsible for storing the detections locally.

    It is called after the model has run. This should decide:

    1. If the detection should be stored
    2. How the detection should be stored
    """

    @abstractmethod
    def get_current_deployment(self) -> Deployment:
        """Get the current deployment from the local filesystem."""

    @abstractmethod
    def store_deployment(self, deployment: Deployment) -> None:
        """Store the deployment locally."""

    @abstractmethod
    def store_recording(
        self,
        recording: Recording,
        deployment: Optional[Deployment] = None,
    ) -> None:
        """Store the recording locally.

        If the deployment is not provided, it should be retrieved from
        the local filesystem.
        """

    @abstractmethod
    def store_detections(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> None:
        """Store the detection locally."""


class RecordingFilter(ABC):
    """Determine if a recording should be kept.

    The RecordingFilter is responsible for determining if a recording
    should be kept or deleted. It can use the detections, the recording
    itself, and internal state to determine if the recording should be kept.
    """

    @abstractmethod
    def should_keep_recording(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> bool:
        """Determine if the recording should be kept."""


class RecordingManager(ABC):
    """Save and delete recordings.

    The RecordingManager is responsible for saving and deleting recordings.
    """

    @abstractmethod
    def save_recording(self, recording: Recording) -> None:
        """Save the recording to the local filesystem."""

    @abstractmethod
    def delete_recording(self, recording: Recording) -> None:
        """Delete the recording."""
