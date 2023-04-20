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


    def should_keep_detections(self, detections: List[Detection]) -> bool:
        """
        Args:
            detections: Detections in a recording.   
        Returns:
            bool 
        """
        return any(annotation for annotation in detections if annotation['det_prob'] >= self.threshold)


    def get_clean_detections(self, detections: List[Detection], bool: bool) -> List[Detection]:
        """Get detection and clean them before saving."""
        if bool == True:
            get_cleandetections = [annotation for annotation in detections if annotation['det_prob'] >= self.threshold]
        else:
            get_cleandetections = []
        return get_cleandetections



## class HighestbySpecies_DetectionFilter(DetectionFilter):
## 
##     def __init__(self, threshold: float):
##         """ Initiatlise the filter.
##         
##         Args: 
##             threshold: The probability threshold to be used.
##         """ 
##         self.threshold = threshold
##     
##     def should_keep_detections(self, detections: List[Detection]) -> bool:
## 
##         # Create new dictionary to keep the detections
##         keep_detections = []
## 
##         # Loop through all the detections in the analysed file 
##         for ann in self.detections:
##             bat_class = ann['class']
##             det_prob = ann['det_prob']
## 
##             # Check if the detection probability is above the threshold
##             if det_prob > self.threshold:
##                 # Check if bat_class is already in final result list keep_detection
##                 if bat_class not in keep_detections:
##                     keep_detections[bat_class] = ann
##                 else:
##                     # Check if det_prob is higher than the previous final result in list keep_detections
##                     if det_prob > keep_detections[bat_class]['det_prob']:
##                         keep_detections[bat_class] = ann
##         
##         return keep_detections
