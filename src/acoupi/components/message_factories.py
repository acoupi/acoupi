"""Message factories for acoupi.

Message factories are responsible for building messages from model outputs.
Messages are intended to be sent to remote servers using communication
protocols (e.g., MQTT, HTTP) for further processing, storage, or analysis.

The message factories are useful to filter outputs from the model according
to various criteria, avoiding sending unnecessary information to a server,
when connectivity is limited. For example, message factories
can be used to filter detections with low probability.

Message factories are implemented as classes that inherit from MessageBuilder. The class should
implement the build_message method, which takes a model output and returns a message. The message
should be a JSON string containing the information to be sent to the remote server.
"""

from typing import List, Optional

from acoupi import data
from acoupi.components import types

__all__ = [
    "DetectionThresholdMessageBuilder",
    "FullModelOutputMessageBuilder",
]


class DetectionThresholdMessageBuilder(types.MessageBuilder):
    """A MessageBuilder that builds message from model outputs.

    This message builder builds a message from a model output. The created
    message will contain the full model output as a JSON string. This
    includes information about the model used, the recording including deployment info,
    and the detections and predicted tags that meet the threshold.
    """

    def __init__(self, detection_threshold: float):
        """Remove detections that do not meet the threshold."""
        self.detection_threshold = detection_threshold

    def filter_detections(
        self, detections: List[data.Detection]
    ) -> List[data.Detection]:
        """Remove detections with low probability."""
        return [
            detection
            for detection in detections
            if detection.detection_probability >= self.detection_threshold
            and detection.tags != []
        ]

    def build_message(
        self, model_output: data.ModelOutput
    ) -> Optional[data.Message]:
        """Build a message with only detections meeting threshold.

        Parameters
        ----------
        self.detection_threshold: float
            The minimum detection probability required for a detection to be included in the message.
        self.filter_detections: List[data.Detection]
            A list of detections from the model_output.detections to be filtered.
        model_output: data.ModelOutput
            The model output to build the message from.

        Returns
        -------
            A message containing the model output or None if no valid detections.

        Examples
        --------
        >>> model_output = data.ModelOutput(
        ...     data.Detection(
        ...         detection_probability=0.5,
        ...         tags=[
        ...             data.PredictedTag(
        ...                 tag=data.Tag(
        ...                     key="species", value="species_1"
        ...                 ),
        ...                 classification_probability=0.4,
        ...             )
        ...         ],
        ...     )
        ... )
        >>> message_builder = DetectionThresholdMessageBuilder(
        ...     detection_threshold=0.6
        ... )
        >>> message_builder.build_message(model_output)
        None

        >>> model_output = data.ModelOutput(
        ...     data.Detection(
        ...         detection_probability=0.9,
        ...         tags=[
        ...             data.PredictedTag(
        ...                 tag=data.Tag(
        ...                     key="species", value="species_1"
        ...                 ),
        ...                 classification_probability=0.9,
        ...             )
        ...         ],
        ...     )
        ... )
        >>> message_builder = DetectionThresholdMessageBuilder(
        ...     detection_threshold=0.6
        ... )
        >>> message_builder.build_message(model_output)
        Message(content='{"name_model": "TestModel", "recording": {"path": "recording.wav", "deployment": {}, "tags": [], "detections": [{"detection_probability": 0.9, "location": {}, "tags": [{"tag": {"key": "species", "value": "species_1"}, "classification_probability": 0.9}]}]}')
        """
        filtered_detections = self.filter_detections(model_output.detections)
        if not filtered_detections:
            return None

        # Clean model output
        filtered_model_output = data.ModelOutput(
            name_model=model_output.name_model,
            recording=model_output.recording,
            tags=model_output.tags,
            detections=filtered_detections,
        )
        return data.Message(content=filtered_model_output.model_dump_json())


class FullModelOutputMessageBuilder(types.MessageBuilder):
    """A MessageBuilder that builds message from model outputs.

    This message builder builds a message from a model output. The created
    message will contain the full model output as a JSON string.
    """

    def build_message(self, model_output: data.ModelOutput) -> data.Message:
        """Build a message from a recording and model outputs.

        Parameters
        ----------
        model_output: data.ModelOutput
            The model output to build the message from.

        Returns
        -------
            A message containing the full model output.
        """
        return data.Message(content=model_output.model_dump_json())
