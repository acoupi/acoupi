"""Model output cleaners."""
from typing import List

from acoupi.components.types import ModelOutputCleaner
from acoupi.data import Detection, ModelOutput, PredictedTag

class ThresholdDetectionFilter(ModelOutputCleaner):
    """Keeps predictions with a probability above a threshold.

    This class implements a model output cleaner that removes any
    predictions with a probability below a threshold. This includes
    removing low confidence tags and detections.
    """
    
    def __init__(self, threshold: float):
        """ Initiatlise the filter.
        
        Args: 
            threshold: The probability threshold to be used.
        """ 
        self.threshold = threshold

    def get_clean_tags(self, tags: List[PredictedTag]) -> List[PredictedTag]:
        """Removes tags with low probability."""
        return [
            tag for tag in tags 
            if tag.probability >= self.threshold
        ]

    def get_clean_detections(
        self, detections: List[Detection]
    ) -> List[Detection]:
        """Removes detections with low probability."""
        return [
            self.clean_detection(detection)
            for detection in detections
            if detection.probability >= self.threshold
        ]

    def clean_detection(self, detection: Detection) -> Detection:
        """Removes tags with low probability from detection."""
        return Detection(
            id=detection.id,
            location=detection.location,
            probability=detection.probability,
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
            model_name=model_output.model_name,
            recording=model_output.recording,
            tags=self.get_clean_tags(model_output.tags),
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
