""" Run BatDetect2 Model """
from typing import List, Dict
from acoupi.types import Model, Recording, Detection


class BatDetect2(Model):

    "BatDetect2 Model to analyse the audio recording"
    
    def __init__(self, recording: path, detections:Dict[Detections]):

        self.recording = recording
        self.detections = detections

    def runModel():
        return 