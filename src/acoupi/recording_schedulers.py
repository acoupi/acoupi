"""Recording Schedulers for acoupi.

Recording schedulers are used to determine how often recordings should be made.
This is useful for example if you want to record at a constant interval, or if
you want to record at a variable interval, such as every 10 minutes during the
day and every 30 minutes at night.

Recording schedulers are implemented as classes that inherit from 
RecordingScheduler. The class should implement the time_until_next_recording 
method, which returns the time in seconds until the next recording should be 
made.
"""
from acoupi.config import DEFAULT_RECORDING_INTERVAL
from acoupi.types import RecordingScheduler
import datetime

__all__ = [
    "IntervalScheduler",
]


class IntervalScheduler(RecordingScheduler):
    """Will wait for a constant amount of time between each recording."""

    interval: float
    """The interval between each recording. In seconds."""

    def __init__(self, interval: float = DEFAULT_RECORDING_INTERVAL):
        """Initialize the recording scheduler.

        Args:
            interval: The interval between each recording. In seconds.
        """
        self.interval = interval

    def time_until_next_recording(self, time: datetime = None) -> float:
        """Return the number of second until the next recording.
        Should return 0 if a recording should be made immediately. 

        Args:
            time: The time to use for determining the next recording. 
            Defaults to None.
        
        """
        if not time:
            time = datetime.datetime.now()
        next_recording_time = (time + datetime.timedelta(seconds=self.interval)).replace(microsecond=0)
        return int((next_recording_time - time).total_seconds())
        
