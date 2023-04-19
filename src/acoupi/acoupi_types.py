"""This module contains the types used by the aucupi."""
import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
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

    name: str
    """User provided name of the deployment."""

    latitude: Optional[float] = None
    """The latitude of the site where the device is deployed."""

    longitude: Optional[float] = None
    """The longitude of the site where the device is deployed."""

    id: UUID = field(default_factory=uuid4)
    """The unique ID of the deployment."""


@dataclass
class Recording:
    """A Recording is a single audio file recorded from the microphone."""

    path: Optional[str]
    """The path to the audio file in the local filesystem"""

    datetime: datetime.datetime
    """The datetime when the recording was made"""

    duration: float
    """The duration of the recording in seconds"""

    samplerate: int
    """The samplerate of the recording in Hz"""

    id: UUID = field(default_factory=uuid4)
    """The unique ID of the recording"""


@dataclass
class Detection:
    """A Detection is a single prediction from a model."""

    species_name: str
    """The name of the species predicted by the model"""

    probability: float
    """The probability of the prediction"""

    id: UUID = field(default_factory=uuid4)
    """The unique ID of the detection"""


class RecordingScheduler(ABC):
    """Manage time between recordings.

    The RecordingScheduler is responsible for determining the interval between
    recordings.
    """

    @abstractmethod
    def time_until_next_recording(
        self,
        time: Optional[datetime.datetime] = None,
    ) -> int:
        """Return the number of seconds until the next recording.

        This should return 0 if a recording should be made immediately.

        Args:
            time: The time to use for determining the next recording.
                Defaults to None.
        """


class RecordingCondition(ABC):
    """Decide if a recording should be made.

    Only do a recording if the RecordingCondition is met.

    The RecordingCondition is responsible for deciding if a recording
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


class DetectionFilter(ABC):
    """Determine if a detection should be saved.

    The DetectionFilter is responsible for determining if a detection
    should be saved.
    """

    @abstractmethod
    def should_keep_detection(
        self, 
        detection: List[Detection]
    ) -> bool:
        """Determine if the detection should be stored locally."""


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


class SavingManager(ABC):
    """The SavingManager is responsible for saving the recordings
    and detections locally. 
    """

    #@abstractmethod
    #def find_treshold(self, 
    #    treshold: Threshold, 
    #    detections: List[Detection]
    #) -> bool:

    @abstractmethod
    def save_recording(
        self, 
        recording: Recording,
        detections: List[Detection]
    ) -> None:
        """Save the recording locally."""

    @abstractmethod
    def save_detection(
        self, 
        detections: List[Detection]
    ) -> None:
        """Save the detection locally"""


class Store(ABC):
    """The Store is responsible for storing the detections locally.

    The store keeps track of all the recordings, detections, and
    deployments made.
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

    @abstractmethod
    def get_recordings(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[Recording]:
        """Get the recordings from the local filesystem.

        Args:
            include: A list of recording IDs to include. If None, all
                recordings are included.
            exclude: A list of recording IDs to exclude. If None, no
                recordings are excluded. Can not be used simultaneously
                with include.

        Returns:
            A list of recordings.
        """

    @abstractmethod
    def get_detections(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[Detection]:
        """Get the detections from the local filesystem.

        Args:
            include: A list of detection IDs to include. If None, all
                detections are included.
            exclude: A list of detection IDs to exclude. If None, no
                detections are excluded. Can not be used simultaneously
                with include.

        Returns:
            A list of detections.
        """

    @abstractmethod
    def get_deployments(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[Deployment]:
        """Get the deployments from the local filesystem.

        Args:
            include: A list of deployment IDs to include. If None, all
                deployments are included.
            exclude: A list of deployment IDs to exclude. If None, no
                deployments are excluded. Can not be used simultaneously
                with include.

        Returns:
            A list of deployments.
        """

class FileManager(ABC):
    """Save and delete files.

    The FileManager is responsible for saving and deleting recordings
    to the local filesystem.
    """

    @abstractmethod
    def save_recording(self, recording: Recording) -> None:
        """Save the recording to the local filesystem."""

    @abstractmethod
    def delete_recording(self, recording: Recording) -> None:
        """Delete the recording."""


class ResponseStatus(Enum):
    """The status of a message."""

    SUCCESS = "success"
    """The message was received successfully."""

    FAILED = "failed"
    """The message failed to send."""

    ERROR = "error"
    """The message was sent, but there was an error."""

    TIMEOUT = "timeout"
    """The message timed out."""


@dataclass
class Message:
    """The message to be sent to the remote server."""

    sent_on: datetime.datetime
    """The datetime the message was sent."""

    device_id: str
    """The ID of the device sending the message."""

    message: str
    """The message to be sent. Usually a JSON string."""


@dataclass
class Response:
    """The response from sending a message."""

    received_on: datetime.datetime
    """The datetime the message was received."""

    status: ResponseStatus
    """The status of the message."""

    message: Message
    """The message that was sent."""

    content: Optional[str] = None
    """The content of the response."""


class Messenger(ABC):
    """Send messages to a remote server.

    The Messenger is responsible for sending messages to
    a remote server
    """

    @abstractmethod
    def send_message(self, message: Message) -> Response:
        """Send the message to a remote server."""


class MessageStore(ABC):
    """Keeps track of messages that have been sent."""

    store: Store
    """Has access to the local store."""

    @abstractmethod
    def get_unsynced_recordings(self) -> List[Recording]:
        """Get the recordings that have not been synced to the server."""

    @abstractmethod
    def get_unsynced_detections(self) -> List[Detection]:
        """Get the detections that have not been synced to the server."""

    @abstractmethod
    def get_unsynced_deployments(self) -> List[Deployment]:
        """Get the deployments that have not been synced to the server."""

    @abstractmethod
    def store_recording_message(
        self,
        recording: Recording,
        response: Response,
    ) -> None:
        """Register a recording message with the store."""

    @abstractmethod
    def store_deployment_message(
        self,
        deployment: Deployment,
        response: Response,
    ) -> None:
        """Register a deployment message with the store."""

    @abstractmethod
    def store_detection_message(
        self,
        detection: Detection,
        response: Response,
    ) -> None:
        """Register a detection message with the store."""
