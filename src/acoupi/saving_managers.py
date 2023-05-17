""" Saving managers for the recordings and detections of acoupi. 

Saving managers are used to determine where and how the recordings 
and detections of an audio file should be saved. This is helpful to 
handle recordings files and detections outputs, such as recording 
and detections outputs can be saved into a specific format 
(i.e, .wav files, .csv files) and at a specific location 
(i.e, rpi memory, external hardrive, folder XX/YY). 

Saving managers (SavingRecording and SavingDetection) are implemented as classes 
that inherit from RecordingSavingManager and DetectionSavingManager. The classes 
should implement the save_recording and save_detections methods. The save_recording 
method takes the recording object, and the recording filter output. The save_detection
methods also takes a recording object and the detection filter output. On top of these, 
it takes a clean list of detection to be saved. 
"""

from dataclasses import dataclass
from typing import List
import os
import csv
import datetime
from astral import LocationInfo
from astral.sun import sun

from acoupi_types import Recording, RecordingFilter, RecordingSavingManager
from acoupi_types import Detection, DetectionFilter, DetectionSavingManager

__all__ = [
    "SaveRecording",
    "SaveDetection",
]

@dataclass 
class Directories:
    """Directories where file can be savec."""

    dirpath_true: str
    """Directory path to save recordings if audio recording contains detections."""

    dirpath_false: str
    """Directory path to save recordings if audio recording contain no detections."""


class TimeInterval(RecordingSavingManager): 
    """A RecordingSavingManager that save recordings during specific interval of time."""

    def __init__(self, interval:Interval, timezone: datetime.tzinfo):
        """Initiatlise the Interval RecordingSavingManager
        
        Args:
            interval: the interval of time where recordings will be saved.
            timezone: the timezone to use when determining if recording should be saved.
         """
        self.interval = interval
        self.timezone = timezone

    def should_save_recording(self, time: datetime.datetime) -> bool: 
        """Determine if a recording should be saved."""
        return self.interval.start <= time.time() <= self.interval.end


class FrequencySchedule(RecordingSavingManager): 
    """A RecordingSavingManager that save recordings during specific interval of time."""

    def __init__(self, duration:float, frequency:float):
        """Initiatlise the FrequencySchedule RecordingSavingManager
        
        Args:
            duration: the duration (time) for which recordings will be saved. 
            frequency: the interval of time between each time recordings are saved. 
         """

        self.duration = duration
        self.frequency = frequency

    def should_save_recording(self, time: datetime.datetime) -> bool: 
        """Determine if a recording should be saved."""

        time = time or datetime.datetime.now()     
        saving_interval = datetime.timedelta(minutes=self.frequency) - self.duration
        elapsed_time = (time.minute % self.frequency) + (time.second/60)
        
        return elapsed_time < self.duration


class DawnDuskTimeInterval(RecordingSavingManager):
    """A Dawn Time RecordingSavingManager - Record duration after dawn"""
    
    def __init__(self, duration:float, timezone: datetime.tzinfo):
        """Initiatlise the DawnTime RecordingSavingManager
        
        Args:
            duration: the duration after dawn to save recordings.
            timezone: the timezone to use when determining dawntime.
         """
        self.duration = duration
        self.timezone = timezone

    def should_save_recording(self, time: datetime.datetime) -> bool: 
        """Determine if a recording should be saved.
        
            1. Get the sun information for the specific location, datetime and timezone. 
            2. Add the duration of saving recording to the dawntime, dusktime. 
            3. Check if the current time falls within the dawn time interval or dusktime interval.
        """

        current_time = time or datetime.datetime.now(self.timezone)

        sun_info = sun(LocationInfo(self.timezone).observer, date=current_time, tzinfo=self.timezone)
        dawntime = sun_info['dawn']
        dusktime = sun_info['dusk']

        dawntime_interval = dawntime + datetime.timedelta(minutes=self.duration)
        dusktime_interval = dusktime + datetime.timedelta(minutes=self.duration)

        return dawntime_interval <= current_time <= dawntime or dusktime_interval <= current_time <= dusktime


class SaveRecording(RecordingSavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, timeformat: str, save_dir: Directories):
        """Initiatilise the Recording SavingManager.
        
        Args:
            save_dir: Path of the directories where the recording should be saved.
            timeformat: Datetime format to use to name the recording file path.  
        """
        self.save_dir = save_dir
        self.timeformat = timeformat

    def save_recording(self, recording: Recording, bool: RecordingFilter):
        """Determine where and how the recording should be saved.
        
        """
        sdir = self.save_dir.dirpath_true if bool == True else self.save_dir.dirpath_false
        recording_path = recording.path
        srec_filename = recording.datetime.strftime(self.timeformat)
        # Move recording to the path it should be saved
        os.rename(recording_path, ''.join(sdir+'/'+srec_filename)+'.wav')
        return 


class SaveDetection(DetectionSavingManager):
    """A Recording SavingManager that save audio recordings."""

    def __init__(self, timeformat: str, save_dir: Directories):
        """Initiatilise the Recording SavingManager.
        
        Args:
            save_dir: Path of the directories where the detections should be saved.
            timeformat: Datetime format to use to name the detections file path.   
        """
        self.save_dir = save_dir
        self.timeformat = timeformat

    def save_detections(self, recording: Recording, clean_detections: List[Detection], bool: DetectionFilter):
        """Determine where and how the detections should be saved.
        
        """
        sdir = self.save_dir.dirpath_true if bool == True else self.save_dir.dirpath_false
        sdet_filename = recording.datetime.strftime(self.timeformat)

        # Check if clean_detections[] is not empty
        if not clean_detections:
            return

        # Create a file to save the detections
        with open(sdet_filename+'.csv','w', newline='') as csvfile:
            # Create a CSV writer to write the header row and data rows
            writer = csv.DictWriter(csvfile, fieldnames=clean_detections[0].__dict__.keys()) if clean_detections else None
            writer.writeheader()
            writer.writerows({**detection.__dict__} for detection in clean_detections)

        # Move the detection file to the path it should be saved
        os.rename(sdet_filename+'.csv', ''.join(sdir+'/'+sdet_filename+'.csv'))
        return 
