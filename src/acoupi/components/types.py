"""This module contains the types used by the aucupi."""
import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

from acoupi.data import Deployment, Message, ModelOutput, Recording, Response


class RecordingScheduler(ABC):
    """Manage time between recordings.

    The RecordingScheduler is responsible for determining the interval between
    recordings.
    """

    @abstractmethod
    def time_until_next_recording(
        self,
        time: Optional[datetime.datetime] = None,
    ) -> float:
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
    def record(self, deployment: Deployment) -> Recording:
        """Record audio from the microphone and return the recording.

        The recording should be saved to a temporary file and the path
        to the file should be returned, along with the datetime, duration,
        and samplerate of the recording.

        The temporary file should be placed in memory.
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
    ) -> ModelOutput:
        """Run the model on the audio file and return the result.

        Can optionally use deployment info to enhance predictions.
        """


class ModelOutputCleaner(ABC):
    """Clean the model output.

    The ModelOutputCleaner is responsible for cleaning the model output.
    This can include removing detections that are too short, too long,
    have a specific label or low confidence.
    """

    @abstractmethod
    def clean(self, model_output: ModelOutput) -> ModelOutput:
        """Clean the model output."""


class RecordingSavingFilter(ABC):
    """Determine if a recording should be saved.

    The Recording SavingFilter is responsible for deciding if recording should
    be saved.
    """

    @abstractmethod
    def should_save_recording(
        self,
        recording: Recording,
        model_outputs: Optional[List[ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved.

        Args:
            recording: The recording to save.
            model_outputs: Optionally use the model outputs to determine if
                the recording should be saved.
        """


class RecordingSavingManager(ABC):
    """The Recording SavingManager is responsible for saving recordings."""

    @abstractmethod
    def save_recording(
        self,
        recording: Recording,
        model_outputs: Optional[List[ModelOutput]] = None,
    ) -> Path:
        """Save the recording locally.

        Args:
            recording: The recording to save.
            model_outputs: Optionally use the model outputs to determine where
                to save the recording.

        Returns:
            The path to the saved recording.
        """


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

        Args:
            recording: The recording to store.
            deployment: The deployment to store the recording under.
        """

    @abstractmethod
    def store_model_output(
        self,
        model_output: ModelOutput,
    ) -> None:
        """Store the model output locally."""

    @abstractmethod
    def get_recordings(
        self,
        ids: List[UUID],
    ) -> List[Tuple[Recording, List[ModelOutput]]]:
        """Get a list recordings from the store by their ids.

        Each recording is returned with the full list of model outputs
        registered.

        Args:
            ids: The ids of the recordings to get.

        Returns:
            A list of tuples of the recording and the model outputs.
        """

    @abstractmethod
    def update_recording_path(
        self,
        recording: Recording,
        path: Path,
    ) -> Recording:
        """Update the path of the recording."""


class ModelOutputMessageBuilder(ABC):
    """Build a message from the model output.

    The ModelOutputMessageBuilder is responsible for building a message
    from the model output.
    """

    @abstractmethod
    def build_message(
        self,
        model_output: ModelOutput,
    ) -> Message:
        """Build a message from the model output."""


class RecordingMessageBuilder(ABC):
    """Build a message from the recording.

    The RecordingMessageBuilder is responsible for building a message
    from the recording.
    """

    @abstractmethod
    def build_message(
        self,
        recording: Recording,
    ) -> Message:
        """Build a message from the recording."""


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

    @abstractmethod
    def get_unsent_messages(self) -> List[Message]:
        """Get the recordings that have not been synced to the server."""

    @abstractmethod
    def store_message(
        self,
        message: Message,
    ) -> None:
        """Register a message with the store."""

    @abstractmethod
    def store_response(
        self,
        response: Response,
    ) -> None:
        """Register a message response with the store."""
