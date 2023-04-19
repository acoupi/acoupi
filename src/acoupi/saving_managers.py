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
from config import RECORDING_DIR_TRUE, RECORDING_DIR_FALSE 

@dataclass 
class Directories:
    """Directories where file can be savec."""

    dirpath_true: str
    """Directory path to save recordings if audio recording contains detections."""

    dirpath_false: str
    """Directory path to save recordings if audio recording contain no detections."""


class RecordingSavingManager(SavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, recording: Recording, save_dir: Directories):
        """Initiatilise the Recording SavingManager.
        
        Args:
            recording: The audio recording to be saved. 
            save_dir: Path of the directories where the recording should be saved.  
        """
        self.recording = recording
        self.save_dir = save_dir
    
    def save_recording(self, bool: RecordingFilter):
        """Determine where and how the recording should be saved.

        """
        saving_dir = self.save_dir.dirpath_true if bool == True else self.save_dir.dirpath_false
        print(f'Saving Directory: {saving_dir}')
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
