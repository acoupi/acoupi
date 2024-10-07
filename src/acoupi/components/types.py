"""Module containing the types used by the acoupi."""

import datetime
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, List, Optional, Protocol, Tuple
from uuid import UUID

from acoupi import data

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


class RecordingScheduler(ABC):
    """Manage time between recordings.

    The RecordingScheduler is responsible for determining the when recording
    should be made.

    See Also
    --------
    See the module
    [recording_schedulers][acoupi.components.recording_schedulers] for a
    concrete implementation of the RecordingScheduler.

    * [IntervalScheduler][acoupi.components.recording_schedulers.IntervalScheduler]:
        Record at a fixed interval.
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
    See the module
    [recording_conditions][acoupi.components.recording_conditions] for concrete
    implementations of the RecordingCondition.

    * [IsInInterval][acoupi.components.recording_conditions.IsInInterval]:
        Record if the current time is within a specified interval.
    """

    @abstractmethod
    def should_record(self) -> bool:
        """Determine if a recording should be made.

        Returns
        -------
        bool
            True if a recording should be made, False otherwise.
        """


class AudioRecorder(ABC):
    """Record audio from the microphone."""

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
    """Determine if a recording should be processed by a model.

    The ProcessingFilter is responsible for determining if a recording
    should be processed by the model.
    """

    @abstractmethod
    def should_process_recording(self, recording: data.Recording) -> bool:
        """Determine if the recording should be processed by the model.

        Parameters
        ----------
        recording
            The recording to check.

        Returns
        -------
        should_process
             True if the recording should be processed, False otherwise.
        """


class Model(Protocol):
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

        Parameters
        ----------
        recording
            The recording to process.

        Returns
        -------
        model_output
            The model output containing the detections.
        """


class ModelOutputCleaner(ABC):
    """Clean the model output.

    The ModelOutputCleaner is responsible for cleaning the model output.
    This can include removing detections that are too short, too long,
    have a specific label or low confidence.

    Notes
    -----
    Model output cleaners are particularly useful when using a pre-trained
    model that produces irrelevant predictions. This component helps prune
    those predictions to make them more relevant to the task at hand.

    See Also
    --------
    See the module [output_cleaners][acoupi.components.output_cleaners] for a
    concrete implementation of the ModelOutputCleaner.

    * [ThresholdDetectionCleaner][acoupi.components.output_cleaners.ThresholdDetectionCleaner]:
        Keeps only the classifcations and dectections that are equal or higher than a threshold.
    """

    @abstractmethod
    def clean(self, model_output: data.ModelOutput) -> data.ModelOutput:
        """Clean the model output.

        This method will remove any predicted tag or detection that does not meet the
        specified criteria.

        Parameters
        ----------
        model_output : data.ModelOutput
            The model output to clean.

        Returns
        -------
        data.ModelOutput
            The cleaned model output.
        """


class RecordingSavingFilter(ABC):
    """The Recording Saving Filter is responsible for determining if a recording should be saved.

    Notes
    -----
    The RecordingSavingFilter is responsible for determining if a recording
    should be saved. The RecordingSavingFilter is used by the management task.
    If the boolean value returned is True, the recording will be saved. If
    False, the recording will be deleted.

    See Also
    --------
    See [saving_filters][acoupi.components.saving_filters]
    for concrete implementations of the RecordingSavingFilter.

    * [After_DawnDuskTimeInterval][acoupi.components.saving_filters.After_DawnDuskTimeInterval] / [Before_DawnDuskTimeInterval][acoupi.components.saving_filters.Before_DawnDuskTimeInterval]:
        Save recordings if they falls withing a specified time interval
        happening after or before astronomical dawn and dusk.
    * [SavingThreshold][acoupi.components.saving_filters.SavingThreshold]:
        Save recordings if any of the detection and classification tag score associated to
        the recording model output is higher or equal than a specified threshold.
    * [SaveIfInInterval][acoupi.components.saving_filters.SaveIfInInterval]:
        Save recordings if the recording falls within a specified interval.
    * [FrequencySchedule][acoupi.components.saving_filters.FrequencySchedule]:
        Save recordings if the recording falls within the specified frequency schedule.
    """

    @abstractmethod
    def should_save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> bool:
        """Determine if a recording should be saved.

        Parameters
        ----------
        recording : data.Recording
            The recording to check.
        model_outputs : Optional[List[data.ModelOutput]], optional
            The model outputs associated to the recording. Used in
            some implementations when the decision to save a recording
            depends on the model outputs, rather the recording itself.

        Returns
        -------
        bool
            True if the recording should be saved, False otherwise.
        """


class RecordingSavingManager(ABC):
    """The Recording SavingManager is responsible for saving recordings.

    Notes
    -----
    The RecordingSavingManager is responsible for saving recordings. The
    RecordingSavingManager is used by the management task. The
    RecordingSavingManager is used to save recordings to the correct path.

    See Also
    --------
    See the module [saving_managers][acoupi.components.saving_managers] for
    concrete implementations of the RecordingSavingManager.

    * [SaveRecordingManager][acoupi.components.saving_managers.SaveRecordingManager]:
        Save recordings to a specified directory according to the model outputs.
    * [DateFileManager][acoupi.components.saving_managers.DateFileManager]:
        Save recordings to directories based on the date of the recording.
    """

    @abstractmethod
    def save_recording(
        self,
        recording: data.Recording,
        model_outputs: Optional[List[data.ModelOutput]] = None,
    ) -> Path:
        """Save the recording.

        Parameters
        ----------
        recording : data.Recording
            The recording to save.
        model_outputs : Optional[List[data.ModelOutput]], optional
            The model outputs associated to the recording. Used to determined
            where and how to save the recording.

        Returns
        -------
        Path
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

        Parameters
        ----------
        recording : data.Recording
            The recording to store.
        deployment : Optional[data.Deployment], optional
            The deployment associated with the recording, by default None.
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

        Parameters
        ----------
        ids : List[UUID]
            The ids of the recordings to get.

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

        Parameters
        ----------
        paths : List[Path]
            The paths of the recordings to get.

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

    See Also
    --------
    See the module [message_factories][acoupi.components.message_factories] for
    concrete implementations of the MessageBuilder.

    * [DetectionThresholdMessageBuilder][acoupi.components.message_factories.DetectionThresholdMessageBuilder]:
        Filters detections by a score threshold.

    * [FullModelOutputMessageBuilder][acoupi.components.message_factories.FullModelOutputMessageBuilder]:
        No filtering. Format the entire model output.
    """

    @abstractmethod
    def build_message(
        self,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Optional[data.Message]:
        """Will build a message or return None depending on the input data.

        Returns
        -------
        Optional[data.Message]
            The assembled message or None if the input data is not suitable.

        """


class Summariser(ABC):
    """Summarise model outputs.

    The Summariser is responsible for summarising model outputs
    (i.e., detections) into a message.

    See Also
    --------
    See the module [summarisers][acoupi.components.summariser] for concrete
    implementations of the Summariser.

    * [StatisticsDetectionsSummariser][acoupi.components.summariser.StatisticsDetectionsSummariser]:
        Summarises detections by calculating the mean, min, max, and count of
        classification probabilities for each species.

    * [ThresholdsDetectionsSummariser][acoupi.components.summariser.ThresholdsDetectionsSummariser]:
        Count the number of detections for each species that falls into three
        thresholds different bands: low, medium, and high.
    """

    @abstractmethod
    def build_summary(
        self,
        now: datetime.datetime,
    ) -> data.Message:
        """Build a summary.

        Parameters
        ----------
        now : datetime.datetime
            The time of the summary.

        Returns
        -------
        data.Message
            The summary as a data.Message object. The message should be in JSON format.
        """


class Messenger(ABC):
    """Send messages.

    The Messenger is responsible for sending messages to a remote server
    according to communication protocol.

    See Also
    --------
    See the module [messenger][acoupi.components.messengers] for concrete
    implementations of the Messenger.

    * [MQTTMessenger][acoupi.components.messengers.MQTTMessenger]:
        Send messages using the MQTT protocol.

    * [HTTPMessenger][acoupi.components.messengers.HTTPMessenger]:
        Send messages using the HTTP POST Request.
    """

    @abstractmethod
    def send_message(self, message: data.Message) -> data.Response:
        """Send the message to a remote server.

        Parameters
        ----------
        message : data.Message
            The message to send.

        Returns
        -------
        data.Response
            A response containing the message, status, content, and received time.
        """


class MessageStore(ABC):
    """Keeps track of messages that have been produced and sent."""

    @abstractmethod
    def get_unsent_messages(self) -> List[data.Message]:
        """Get the recordings that have not been synced to the server.

        Returns
        -------
        List[data.Message]
            A list of unsent messages.
        """

    @abstractmethod
    def store_message(
        self,
        message: data.Message,
    ) -> None:
        """Register a message with the store.

        Parameters
        ----------
        message
            Store a message.
        """

    @abstractmethod
    def store_response(
        self,
        response: data.Response,
    ) -> None:
        """Register a message response with the store.

        Parameters
        ----------
        response
            Store the server response.
        """
