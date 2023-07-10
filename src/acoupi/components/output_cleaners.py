"""Model output cleaners."""
from typing import List, Optional

from acoupi.components.types import ModelOutputCleaner
from acoupi.data import Detection, ModelOutput


class ThresholdDetectionFilter(ModelOutputCleaner):
    """Keeps predictions with a probability above a threshold.

    This class implements a model output cleaner that removes any
    predictions with a probability below a threshold. This only includes
    removing detections.

    Additionally it can be configured to only keep detections that have a
    tag with a specific key. This is useful when the model detects
    non-species specific tags, such as "noise" or "unknown" tags, and you
    only want to keep detections that have a species specific tag.
    """

    def __init__(self, threshold: float, tag_keys: Optional[List[str]] = None):
        """Initialise the filter.

        Parameters
        ----------
        threshold: float
            The probability threshold to be used.

        tag_keys: Optional[List[str]]
            Tag keys to be monitored. Will only keep detections that have a tag
            from with one of the specified keys. The tag probability is not
            considered when filtering. If None, detections will be kept
            regardless of the tag key. Defaults to None.

        """
        self.threshold = threshold
        self.tag_keys = tag_keys

    def get_clean_detections(
        self, detections: List[Detection]
    ) -> List[Detection]:
        """Removes detections with low probability."""
        return [
            detection
            for detection in detections
            if not self.should_remove_detection(detection)
        ]

    def should_remove_detection(self, detection: Detection) -> bool:
        """Determine if detection should be removed."""
        if detection.probability < self.threshold:
            return True

        if self.tag_keys is None:
            return False

        for tag in detection.tags:
            if tag.tag.key in self.tag_keys:
                return False

        return True

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
            model_name=model_output.model_name,
            recording=model_output.recording,
            tags=model_output.tags,
            detections=self.get_clean_detections(model_output.detections),
        )


# TODO: Update this class to a ModelOutputCleaner and new ModelOutput and
# Detection classes.

# class HighestbySpecies_DetectionFilter(ModelOutputCleaner):
#     def __init__(self, threshold: float):
#         """Initiatlise the filter.
#
#         Args:
#             threshold: Probability threshold to be used. Only keep detection
#             annotations with a probability greater or equal to this
#             threshold.
#         """
#         self.threshold = threshold
#
#     def should_store_detection(self, detections: List[Detection]) -> bool:
#         # Create new dictionary to keep the detections
#         keep_detections = []
#
#         # Loop through all the detections in the analysed file
#         for ann in detections:
#             bat_class = ann["class"]
#             det_prob = ann["det_prob"]
#
#             # Check if the detection probability is above the threshold
#             if det_prob > self.threshold:
#                 # Check if bat_class is already in final result list
#                 # keep_detection
#                 if bat_class not in keep_detections:
#                     keep_detections[bat_class] = ann
#                 else:
#                     # Check if det_prob is higher than the previous final
#                     # result in list keep_detections
#                     if det_prob > keep_detections[bat_class]["det_prob"]:
#                         keep_detections[bat_class] = ann
#
#         return keep_detections
