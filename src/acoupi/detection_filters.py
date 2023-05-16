from typing import List, Dict
from acoupi_types import Detection, DetectionFilter

#from acoupi.types import Detection, DetectionFilter


class ThresholdDetectionFilter(DetectionFilter):
    """A DetectionFilter that keeps annotations with confident probability of detection.

    This filter will keep all the detection annotations from the model output that are above a
    threshold argument. The threshold argument can be used to set the minimum probability 
    threshold for an annotation to be considered confident.
    """

    def __init__(self, threshold: float):
        """ Initiatlise the filter.
        
        Args: 
            threshold: Probability threshold to be used.
        """ 
        self.threshold = threshold


    def should_store_detection(self, detections: List[Detection]) -> bool:
        """
        Args:
            detections: Detections in a recording.   
        Returns:
            bool 
        """
        return any(annotation for annotation in detections if annotation['det_prob'] >= self.threshold)
        

    def get_clean_detections_obj(self, detections: List[Detection], bool: bool) -> List[Detection]:
        """Get detection and clean them before saving."""
        if bool == True:
            get_cleandetections = [annotation for annotation in detections if annotation['det_prob'] >= self.threshold]
            
            cleandetection_obj = [Detection(species_name = detection['class'],
                                class_probability = detection['class_prob'],
                                soundevent_probability = detection['det_prob'],
                                soundevent_start_time = detection['start_time'],
                                soundevent_end_time = detection['end_time'],
                                ) for detection in get_cleandetections] 
        else:
            get_cleandetections = []
        return cleandetection_obj



class HighestbySpecies_DetectionFilter(DetectionFilter):

    def __init__(self, threshold: float):
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
        
        return keep_detections
