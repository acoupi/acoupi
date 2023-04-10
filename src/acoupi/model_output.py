""" Cleaning Model Output """
from typing import List, Dict
from acoupi_types import Detection
from config import DETECTION_THRESHOLD
#from acoupi.types import Detection

# run the model
# detections = du.process_file(audio_file, model, params, args, max_duration=max_duration)


class CleanModelOutput():

    def __init__(self, detection: Detection, threshold: float = DETECTION_THRESHOLD):

       self.detection = detection
       self.threshold = threshold


    def getDetection_aboveThreshold(self):
        
        # Iterate through all detections - Keep only the one above threshold
        keep_detections = [ann for ann in self.detection if ann['det_prob'] > self.threshold]

        return keep_detections

        
    def getDetection_highestbySpecies(self):
        
        # Create new dictionary to keep the detections
        keep_detections = []

        # Loop through all the detections in the analysed file 
        for ann in self.detection:
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

