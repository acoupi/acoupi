from typing import List, Dict
from acoupi_types import Detection, DetectionFilter

class ThresholdDetectionFilter(DetectionFilter):
    """A DetectionFilter that return True or False if any of the detections are above 
    a specified threshold. The threshold argument can be used to set the minimum probability 
    threshold for an annotation to be considered confident.

    IF True : Detections are likely to have identify a bat call. 
    IF False: Detections are unlikely to have identify a bat call. 

    The result of ThresholdDetectionFilter is used by the SavingManagers. It tells the 
    SavingManager how to save detections.
    """

    def __init__(self, threshold: float):
        """ Initiatlise the filter.
        
        Args: 
            threshold: The probability threshold to be used.
        """ 
        self.threshold = threshold

    def should_keep_detection(self, detections: List[Detection]) -> bool:

        """
        Args:
            detections: Detections in a recording.

        Returns:
            bool
        """

        return any(
            annotation for annotation in detections if annotation['det_prob'] >= self.threshold
        )


class HighestbySpecies_DetectionFilter(DetectionFilter):

    def __init__(self, threshold: float):
        """ Initiatlise the filter.
        
        Args: 
            threshold: The probability threshold to be used.
        """ 
        self.threshold = threshold
    
    def should_keep_detection(self, detections: List[Detection]) -> bool:

        # Create new dictionary to keep the detections
        keep_detections = []

        # Loop through all the detections in the analysed file 
        for ann in self.detections:
            bat_class = ann['class']
            det_prob = ann['det_prob']

            # Check if the detection probability is above the threshold
            if det_prob > self.threshold:
                # Check if bat_class is already in final result list keep_detection
                if bat_class not in keep_detections:
                    keep_detections[bat_class] = ann
                else:
                    # Check if det_prob is higher than the previous final result in list keep_detections
                    if det_prob > keep_detections[bat_class]['det_prob']:
                        keep_detections[bat_class] = ann
        
        return keep_detections



##. class BoolDetectionFilter(DetectionFilter):
##.     """Determine if recording detects Bats."""
##.     
##.     def __init__(self, threshold: float = DETECTION_THRESHOLD):
##.         """Initialise the filter. 
##.         Args: 
##.             threshold: Probability threshold to be used. Return True if some detections
##.             are above threshold, return False if detection are below threshod.
##.         """
##.     def save_manager(self, detections: List[Detection]) -> bool:
##.         return any(detection.det_prob >= self.threshold for detection in detections)
