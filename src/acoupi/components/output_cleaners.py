"""Model output cleaners."""
from typing import List

from acoupi import data
from acoupi.components.types import ModelOutputCleaner

__all__ = [
    "DetectionProbabilityCleaner",
    "TagKeyCleaner",
]

class DetectionProbabilityCleaner(ModelOutputCleaner):
    """Keeps predictions with a probability above a threshold.

    This class implements a model output cleaner that removes any
    predictions with a probability below a threshold. This only includes
    removing detections and not predicted tags at the recording level.
    """

    def __init__(self, threshold: float):
        """Initialise the filter.

        Parameters
        ----------
        threshold: float
            The probability threshold to be used.

        """
        self.threshold = threshold

    def get_clean_detections(
        self, detections: List[data.Detection]
    ) -> List[data.Detection]:
        """Removes detections with low probability."""
        return [
            detection
            for detection in detections
            if detection.probability >= self.threshold
        ]

    def clean(self, model_output: data.ModelOutput) -> data.ModelOutput:
        """Clean the model output.

        This methods will remove any detection with a probability below the
        threshold.

        Parameters
        ----------
        model_output: data.ModelOutput
            The model output to clean.

        Returns
        -------
        data.ModelOutput
            The cleaned model output.
        """
        return data.ModelOutput(
            model_name=model_output.model_name,
            recording=model_output.recording,
            tags=model_output.tags,
            detections=self.get_clean_detections(model_output.detections),
        )


class TagProbabilityThresholdCleaner(ModelOutputCleaner):
    """Keeps tags with a probability above a threshold.

    This class implements a model output cleaner that removes any predicted
    tags with a probability below a threshold. This only includes removing
    predicted tags, and will not remove any detection.
    """

    def __init__(self, threshold: float):
        """Initialise the filter.

        Parameters
        ----------
        threshold: float
            The probability threshold to be used.

        """
        self.threshold = threshold

    def get_clean_tags(
        self, tags: List[data.PredictedTag]
    ) -> List[data.PredictedTag]:
        """Removes tags with low probability."""
        return [tag for tag in tags if tag.probability >= self.threshold]

    def get_clean_detection(self, detection: data.Detection) -> data.Detection:
        """Removes tags with low probability."""
        return data.Detection(
            id=detection.id,
            location=detection.location,
            probability=detection.probability,
            tags=self.get_clean_tags(detection.tags),
        )

    def clean(self, model_output: data.ModelOutput) -> data.ModelOutput:
        """Clean the model output.

        This methods will remove any predicted tag or detection with a
        probability below the threshold.

        Args:
            model_output: The model output to clean.

        Returns:
            The cleaned model output.
        """
        return data.ModelOutput(
            model_name=model_output.model_name,
            recording=model_output.recording,
            tags=self.get_clean_tags(model_output.tags),
            detections=[
                self.get_clean_detection(detection)
                for detection in model_output.detections
            ],
        )


class TagKeyCleaner(ModelOutputCleaner):
    """Cleaner that only keeps detections that have a tag with a specific keys.

    Optionally can remove all other tags from the detections.
    """

    def __init__(self, tag_keys: List[str], remove_other_tags: bool = True):
        """Initialise the filter.

        Parameters
        ----------
        tag_keys: List[str]
            The tag keys to keep.

        remove_other_tags: bool
            If True, all tags that are not in the tag_keys will be removed from
            the detections. Defaults to True.

        """
        self.tag_keys = tag_keys
        self.remove_other_tags = remove_other_tags

    def clean_tags(
        self, tags: List[data.PredictedTag]
    ) -> List[data.PredictedTag]:
        """Remove tags that are not in the tag_keys."""
        if not self.remove_other_tags:
            return tags

        return [tag for tag in tags if tag.tag.key in self.tag_keys]

    def should_keep_detection(self, detection: data.Detection) -> bool:
        """Determine if detection should be kept."""
        for tag in detection.tags:
            if tag.tag.key in self.tag_keys:
                return True

        return False

    def clean_detection(self, detection: data.Detection) -> data.Detection:
        """Remove tags that are not in the tag_keys."""
        return data.Detection(
            id=detection.id,
            location=detection.location,
            probability=detection.probability,
            tags=self.clean_tags(detection.tags),
        )

    def clean_detections(
        self, detections: List[data.Detection]
    ) -> List[data.Detection]:
        """Remove detections that do not have a tag with a key in the tag_keys."""
        return [
            self.clean_detection(detection)
            for detection in detections
            if self.should_keep_detection(detection)
        ]

    def clean(self, model_output: data.ModelOutput) -> data.ModelOutput:
        """Clean the model output.

        This methods will remove any detections that do not have a tag
        with a key in the tag_keys list.

        If remove_other_tags is True, all tags that are not in the
        tag_keys will be removed from the detections.

        Args:
            model_output: The model output to clean.

        Returns:
            The cleaned model output.
        """
        return data.ModelOutput(
            id=model_output.id,
            model_name=model_output.model_name,
            recording=model_output.recording,
            tags=self.clean_tags(model_output.tags),
            detections=self.clean_detections(model_output.detections),
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
