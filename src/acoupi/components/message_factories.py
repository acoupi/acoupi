"""Message factories for acoupi."""

import json
from typing import Dict, List, Optional

from acoupi import data
from acoupi.components import types

__all__ = [
    "DetectionThresholdMessageBuilder",
    "FullModelOutputMessageBuilder",
    "SummaryMessageBuilder",
]


class DetectionThresholdMessageBuilder(types.MessageBuilder):
    """A MessageBuilder that builds message from model outputs.

    This message builder builds a message from a model output. The created
    message will contain the full model output as a JSON string. This
    includes information about:

    - the model used.
    - the recording processed, including deployment info.
    - the detections and predicted tags that meet the threshold.
    """

    def __init__(self, detection_threshold: float):
        """Initiatlise the message builder.

        Args:
            detection_threshold: the threshold that will be used to filter detections to be kept in the message.
        """
        self.detection_threshold = detection_threshold

    def filter_detections(
        self, detections: List[data.Detection]
    ) -> List[data.Detection]:
        """Remove detections with low probability."""
        return [
            self.clean_detection(detection)
            for detection in detections
            if detection.detection_probability >= self.detection_threshold and detection.tags != []
        ]

    def clean_detection(self, detection: data.Detection) -> data.Detection:
        """Remove tags with low probability from detection."""
        return data.Detection(
            id=detection.id,
            location=detection.location,
            detection_probability=detection.detection_probability,
            tags=detection.tags,
        )

    def build_message(
        self, model_output: data.ModelOutput
    ) -> Optional[data.Message]:
        """Build a message with only detections meeting threshold.

        Args:
            model_output: The model output to build the message from.

        Returns
        -------
            A message containing the model output with only detections meeting the threshold"
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
    message will contain the full model output as a JSON string. This
    includes information about:

    - the model used.
    - the recording processed, including deployment info.
    - the predicted tags at the recording level.
    - predicted detections with their tags and confidence scores.
    """

    def build_message(self, model_output: data.ModelOutput) -> data.Message:
        """Build a message from a recording and model outputs."""
        return data.Message(content=model_output.model_dump_json())


class SummaryMessageBuilder(types.MessageBuilder):
    """A SummaryMessageBuilder that builds message from summariser outputs.

    This mesage builder builds a message from a summary. The created
    message will contain the summary as a JSON string. This includes
    information about:

    - the summary content.
    - the summary timeinterval with starttime and endtime.
    """

    def build_message(
        self, timeinterval: Dict, summary_content: Dict
    ) -> data.Message:
        """Build a message from a recording and model outputs."""
        return data.Message(
            content=json.dumps(
                {
                    "timeinterval": timeinterval,
                    "summary_content": summary_content,
                }
            )
        )
