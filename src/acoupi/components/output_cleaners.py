"""Model output cleaners."""

from typing import List

from acoupi.components.types import ModelOutputCleaner
from acoupi.data import Detection, ModelOutput, PredictedTag


class ThresholdDetectionFilter(ModelOutputCleaner):
    """Keeps predictions with a probability (i.e., classification_probability
    and detection_probability) above a defined threshold.

    This class implements a model output cleaner that removes any
    predictions with a probability below a threshold. This includes
    removing low confidence tags and detections.
    """

    def __init__(self, threshold: float):
        """Initiatlise the filter.

        Args:
            threshold: The probability threshold to be used.
        """
        self.threshold = threshold

    def get_clean_tags(self, tags: List[PredictedTag]) -> List[PredictedTag]:
        """Removes tags with low probability."""
        return [
            tag
            for tag in tags
            if tag.classification_probability >= self.threshold
        ]

    def get_clean_detections(
        self, detections: List[Detection]
    ) -> List[Detection]:
        """Removes detections with low probability."""
        return [
            self.clean_detection(detection)
            for detection in detections
            if detection.detection_probability >= self.threshold
        ]

    def clean_detection(self, detection: Detection) -> Detection:
        """Removes tags with low probability from detection."""
        return Detection(
            id=detection.id,
            location=detection.location,
            detection_probability=detection.detection_probability,
            tags=self.get_clean_tags(detection.tags),
        )

    def clean(self, model_output: ModelOutput) -> ModelOutput:
        """Clean the model output.

        This methods will remove any predicted tag or detection with a
        probability below the threshold.

        Args:
            model_output: The model output to clean.

        Returns:
            The cleaned model output.
        """
        return ModelOutput(
            name_model=model_output.name_model,
            recording=model_output.recording,
            tags=self.get_clean_tags(model_output.tags),
            detections=self.get_clean_detections(model_output.detections),
        )
