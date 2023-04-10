""" Cleaning Model Output """
from typing import List, Dict
from acoupi_types import Detection
#from acoupi.types import Detection

# run the model
# detections = du.process_file(audio_file, model, params, args, max_duration=max_duration)


class CleanModelOutput():

    def __init__(self, detection: Detection):
       
       self.detection = detection


    def get_highest_pdetection(self):
        
        # Create new dictionary to keep the detections
        keep_detections = {}

        # Loop through all the detections in the analysed file 
        for ann in self.detection['pred_dict']['annotation']:
            bat_class = ann['class']
            class_prob = ann['class_prob']
            det_prob = ann['det_prob']
            
            # Keep all the different detected classes 
            if bat_class not in keep_detections:
                keep_detections[bat_class] = {'class_prob': class_prob, 'det_prob': det_prob}
            else:
                # Check class_prob - keep the highest class_prob of all detections
                if class_prob > keep_detections[bat_class]['class_prob']:
                    keep_detections[bat_class]['class_prob'] = class_prob
                    keep_detections[bat_class]['det_prob'] = det_prob
                elif class_prob == keep_detections[bat_class]['class_prob'] and det_prob > keep_detections[bat_class]['det_prob']:
                    keep_detections[bat_class]['det_prob'] = det_prob
        
        return keep_detections

