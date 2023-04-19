""" Saving managers for the recordings and detections of acoupi. 

Saving managers are used to determine where and how the recordings 
and detections of an audio file should be saved. This is helpful to 
handle recordings files and detections outputs, such as recording 
and detections outputs can be saved into a specific format 
(i.e, .wav files, .csv files) and at a specific location 
(i.e, rpi memory, external hardrive, folder XX/YY). 

Saving managers are implemented as classes that inherit from 
SavingManager. The class should implement the XXX method, 
which takes a XXX, XXX, and XXX object. 
"""

from dataclasses import dataclass
from typing import List

from acoupi_types import Detection, Recording, DetectionFilter, RecordingFilter, SavingManager

@dataclass 
class Directories:
    """Directories where file can be savec."""

    dirpath_true: str
    """Directory path to save recordings if audio recording contains detections."""

    dirpath_false: str
    """Directory path to save recordings if audio recording contain no detections."""


class RecordingSavingManager(SavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, save_dir: Directories):
        """Initiatilise the Recording SavingManager.
        
        Args:
            recording: The audio recording to be saved. 
            save_dir: Path of the directories where the recording should be saved.  
        """
        self.save_dir = save_dir
    
    def save_recording(self, recording: Recording, bool: RecordingFilter):
        """Determine where and how the recording should be saved.

        """
        sdir = self.save_dir.dirpath_true if bool == True else self.save_dir.dirpath_false
        recording_filename = self.recording.path
        print(f'Recording Path: {recording_filename}')
    
    ### Recording object = path, datetime, duration, samplerate, id


class DetectionSavingManager(SavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, detections: List[Detection]):
        """Initiatilise the Recording SavingManager.
        
        Args:
            recording: The audio recording to be saved. 
        """
        self.detections = detections
    
    def save_detections(self):
        """Determine where and how the detections should be saved."""
        ...
    
    ### Detection object = species_name, probability
