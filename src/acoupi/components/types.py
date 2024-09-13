"""Module containing the types used by the acoupi."""

import datetime
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, List, Optional, Tuple
from uuid import UUID

from acoupi import data

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


class RecordingScheduler(ABC):
    """Manage time between recordings.

    The RecordingScheduler is responsible for determining the interval between
    recordings.

    See Also
    --------
    `IntervalScheduler` in acoupi.compoments.recording_scheduler for
    a concrete implementation of the RecordingScheduler.
    """

    @abstractmethod
    def time_until_next_recording(
        self,
        time: Optional[datetime.datetime] = None,
    ) -> float:
        """Provide the number of seconds until the next recording.

        Parameters
        ----------
        time : Optional[datetime.datetime], optional
            The time to use for determining the next recording, by default None.

        Returns
        -------
        float
            The number of seconds until the next recording.
            Will return 0 if a recording should be made immediately.
        """


class RecordingCondition(ABC):
    """Decide if a recording should be made.

    Will only do a recording if the RecordingCondition is met.

    See Also
    --------
    IsInInterval in acoupi.components.recording_condition for
    a concrete implementation of the RecordingCondition.
    """

    @abstractmethod
    def should_record(self) -> bool:
        """Determine if a recording should be made."""


class AudioRecorder(ABC):
    """Record audio from the microphone.

    The AudioRecorder is responsible for recording audio from the
    microphone.
    """

    @abstractmethod
    def record(self, deployment: data.Deployment) -> data.Recording:
        """Record audio from the microphone and return the recording.

        Parameters
        ----------
        deployment : data.Deployment
            The deployment to use for recording the audio.

        Returns
        -------
        data.Recording
            The recording that was made. Object containing a temporary recording path,
            along with recording details such as datetime, duration, and samplerate.

        Notes
        -----
        The recording path should be saved in temporary memory until it gets processed.
        The path will be updated after the recording has been processed.
        """


class ProcessingFilter(ABC):
    """Determine if a recording should be processed by the model.

    The ProcessingFilter is responsible for determining if a recording
    should be processed by the model.
    """

    @abstractmethod
    def should_process_recording(self, recording: data.Recording) -> bool:
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
        recording: data.Recording,
    ) -> data.ModelOutput:
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
    def clean(self, model_output: data.ModelOutput) -> data.ModelOutput:
        """Clean the model output."""


class RecordingSavingFilter(ABC):
    """Determine if a recording should be saved.

    The Recording SavingFilter is responsible for deciding if recording should
    be saved.
    """

    @abstractmethod
    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
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
    def saving_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Optional[Path]:
        """Save the recording locally.

        Args:
            recording: The recording to save.
            model_outputs: Optionally use the model outputs to determine where
                to save the recording.

        Returns
        -------
            The path to the saved recording.
        """


class Store(ABC):
    """The Store is responsible for storing the detections locally.

    The store keeps track of all the recordings, detections, and
    deployments made.
    """

    @abstractmethod
    def get_current_deployment(self) -> data.Deployment:
        """Get the current deployment from the local filesystem."""

    @abstractmethod
    def store_deployment(self, deployment: data.Deployment) -> None:
        """Store the deployment locally."""

    @abstractmethod
    def update_deployment(self, deployment: data.Deployment) -> None:
        """Update the deployment."""

    @abstractmethod
    def store_recording(
        self,
        recording: data.Recording,
        deployment: Optional[data.Deployment] = None,
    ) -> None:
        """Store the recording locally.

        Args:
            recording: The recording to store.
            deployment: The deployment to store the recording under.
        """

    @abstractmethod
    def store_model_output(
        self,
        model_output: data.ModelOutput,
    ) -> None:
        """Store the model output locally."""

    @abstractmethod
    def get_recordings(
        self,
        ids: List[UUID],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        """Get a list recordings from the store by their ids.

        Each recording is returned with the full list of model outputs
        registered.

        Args:
            ids: The ids of the recordings to get.

        Returns
        -------
            A list of tuples of the recording and the model outputs.
        """

    @abstractmethod
    def get_recordings_by_path(
        self,
        paths: List[Path],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        """Get a list recordings from the store by their paths.

        Each recording is returned with the full list of model outputs
        registered.

        Args:
            paths: The paths of the recordings to get.

        Returns
        -------
            A list of tuples of the recording and the model outputs.
        """

    @abstractmethod
    def update_recording_path(
        self,
        recording: data.Recording,
        path: Path,
    ) -> data.Recording:
        """Update the path of the recording."""


P = ParamSpec("P")


class MessageBuilder(ABC, Generic[P]):
    """Create messages from input data.

    Returns
    -------
        A message containing the model output or None if no valid detections

    See Also
    --------
    acoupi.components.message_factories for concrete implementations of the MessageBuilder.

    DetectionThresholdMessageBuilder
        Filters detections by a probability threshold.

    FullModelOutputMessageBuilder
        No filtering. Format the entire model output.
    """

    @abstractmethod
    def build_message(
        self,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Optional[data.Message]:
        """Will build a message or return None depending on the input data."""


class Summariser(ABC):
    """Summarise model outputs.

    The Summariser is responsible for summarising model outputs (i.e., detections)
    into a message.
    """

    @abstractmethod
    def build_summary(
        self,
        now: datetime.datetime,
    ) -> data.Message:
        """Send the message to a remote server."""


class Messenger(ABC):
    """Send messages to a remote server.

    The Messenger is responsible for sending messages to
    a remote server
    """

    @abstractmethod
    def send_message(self, message: data.Message) -> data.Response:
        """Send the message to a remote server."""


class MessageStore(ABC):
    """Keeps track of messages that have been sent."""

    @abstractmethod
    def get_unsent_messages(self) -> List[data.Message]:
        """Get the recordings that have not been synced to the server."""

    @abstractmethod
    def store_message(
        self,
        message: data.Message,
    ) -> None:
        """Register a message with the store."""

    @abstractmethod
    def store_response(
        self,
        response: data.Response,
    ) -> None:
        """Register a message response with the store."""
