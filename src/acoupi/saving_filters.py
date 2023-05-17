from dataclasses import dataclass
import datetime
from astral import LocationInfo
from astral.sun import sun

from acoupi_types import Recording, RecordingSavingFilter

__all__ = [
    "TimeInterval",
    "FrequencySchedule",
    "DawnDuskTimeInterval"
]

@dataclass
class Interval:
    """An interval of time between two times of day."""

    start: datetime.time
    """Start time of the interval."""

    end: datetime.time
    """End time of the interval."""


class TimeInterval(RecordingSavingFilter): 
    """A RecordingSavingManager that save recordings during specific interval of time."""

    def __init__(self, interval: Interval, timezone: datetime.tzinfo):
        """Initiatlise the Interval RecordingSavingManager
        
        Args:
            interval: the interval of time where recordings will be saved.
            timezone: the timezone to use when determining if recording should be saved.
         """
        self.interval = interval
        self.timezone = timezone

    #def should_save_recording(self, recording: Recording, time: datetime.datetime) -> bool: 
    def should_save_recording(self, recording: Recording) -> bool:
        """Determine if a recording should be saved."""
        return self.interval.start <= recording.datetime.time() <= self.interval.end


class FrequencySchedule(RecordingSavingFilter): 
    """A RecordingSavingManager that save recordings during specific interval of time."""

    def __init__(self, duration:float, frequency:float):
        """Initiatlise the FrequencySchedule RecordingSavingManager
        
        Args:
            duration: the duration (time) for which recordings will be saved. 
            frequency: the interval of time between each time recordings are saved. 
         """

        self.duration = duration
        self.frequency = frequency

    # def should_save_recording(self, recording: Recording, time: datetime.datetime) -> bool: 
    def should_save_recording(self, recording: Recording) -> bool: 
        """Determine if a recording should be saved."""

        time = recording.datetime  
        saving_interval = datetime.timedelta(minutes=self.frequency) - datetime.timedelta(minutes=self.duration)
        elapsed_time = (time.minute % self.frequency) + (time.second/60)
        
        return elapsed_time < self.duration


class DawnDuskTimeInterval(RecordingSavingFilter):
    """A Dawn Time RecordingSavingManager - Record duration after dawn"""
    
    def __init__(self, duration:float, timezone: datetime.tzinfo):
        """Initiatlise the DawnTime RecordingSavingManager
        
        Args:
            duration: the duration after dawn to save recordings.
            timezone: the timezone to use when determining dawntime.
         """
        self.duration = duration
        self.timezone = timezone
        
    #def should_save_recording(self, time: datetime.datetime) -> bool: 
    def should_save_recording(self, recording: Recording) -> bool:
        """Determine if a recording should be saved.
        
            1. Get the sun information for the specific location, datetime and timezone. 
            2. Add the duration of saving recording to the dawntime, dusktime. 
            3. Check if the current time falls within the dawn time interval or dusktime interval.
        """

        recording_time = recording.datetime.astimezone(self.timezone)
        #current_time = datetime.datetime.now(self.timezone)

        sun_info = sun(LocationInfo(self.timezone).observer, date=recording_time, tzinfo=self.timezone)
        dawntime = sun_info['dawn']
        dusktime = sun_info['dusk']

        dawntime_interval = dawntime + datetime.timedelta(minutes=self.duration)
        dusktime_interval = dusktime + datetime.timedelta(minutes=self.duration)

        return dawntime_interval <= recording_time <= dawntime or dusktime_interval <= recording_time <= dusktime
