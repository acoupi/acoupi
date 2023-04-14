from typing import List, Dict
from acoupi_types import Detection, DetectionFilter
from config import DETECTION_THRESHOLD

#from acoupi.config  import DETECTION_THRESHOLD
#from acoupi.types import Detection, DetectionFilter


class Threshold_DetectionFilter(DetectionFilter):
    """A DetectionFilter that keeps annotations with confident probability of detection.

    This filter will keep all the detection annotations from the model output that are above a
    threshold argument. The threshold argument can be used to set the minimum probability 
    threshold for an annotation to be considered confident.
    """

    def __init__(self, threshold: float = DETECTION_THRESHOLD):
        """ Initiatlise the filter.
        
        Args: 
            threshold: Probability threshold to be used. Only keep detection annotations
            with a probability greater or equal to this threshold.
        """ 
        self.threshold = threshold

    def should_store_detection(self, detections: List[Detection]) -> bool:

        return any(ann for ann in self.detections if ann['det_prob'] >= self.threshold)


class HighestbySpecies_DetectionFilter(DetectionFilter):

    def __init__(self, threshold: float = DETECTION_THRESHOLD):
        """ Initiatlise the filter.
        
        Args: 
            threshold: Probability threshold to be used. Only keep detection annotations
            with a probability greater or equal to this threshold.
        """ 
        self.threshold = threshold
    
    def should_store_detection(self, detections: List[Detection]) -> bool:

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
                    print(keep_detections)
        
        return keep_detections
