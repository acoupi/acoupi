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
import os

from acoupi_types import Recording, RecordingFilter, RecordingSavingManager
from acoupi_types import Detection, DetectionFilter, DetectionSavingManager

@dataclass 
class Directories:
    """Directories where file can be savec."""

    dirpath_true: str
    """Directory path to save recordings if audio recording contains detections."""

    dirpath_false: str
    """Directory path to save recordings if audio recording contain no detections."""


class SaveRecording(RecordingSavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, timeformat: str, save_dir: Directories):
        """Initiatilise the Recording SavingManager.
        
        Args:
            save_dir: Path of the directories where the recording should be saved.  
        """
        self.save_dir = save_dir
        self.timeformat = timeformat

    def save_recording(self, recording: Recording, bool: RecordingFilter):
        """Determine where and how the recording should be saved.

        """
        sdir = self.save_dir.dirpath_true if bool == True else self.save_dir.dirpath_false
        recording_path = recording.path
        recording_filename = recording.datetime.strftime(self.timeformat)
        # Move recording to the path it should be saved
        os.rename(recording_path, "".join(sdir+'/'+recording_filename)+'.wav')
        return 


class SaveDetection(DetectionSavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, timeformat: str, save_dir: Directories):
        """Initiatilise the Recording SavingManager.
        
        Args:
            save_dir: Path of the directories where the detections should be saved.   
        """
        self.save_dir = save_dir
        self.timeformat = timeformat

    def save_detections(self, detections: List[Detection], bool: DetectionFilter):
        """Determine where and how the detections should be saved."""
        sdir = self.save_dir.dirpath_true if bool == True else self.save_dir.dirpath_false
        # Move detection to the path it should be saved
        #
    ### Detection object = species_name, probability
