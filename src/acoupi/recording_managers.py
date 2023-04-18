"""Recording managers for acoupi.

Recording managers are used to determine if a recording should be made at a
specific time. This is useful for example if you want to only record during
specific times of day, such as between 8am and 5pm, or if you want to record
during specific days of the week, such as only on weekdays.

Recording managers are implemented as classes that inherit from RecordManager.
The class should implement the should_record method, which takes a 
datetime.datetime object and returns a boolean indicating if a recording 
should be made at that time.
"""
import datetime
from dataclasses import dataclass
from typing import List

from acoupi.types import RecordManager

__all__ = [
    "IntervalRecordingManager",
    "MultiIntervalRecordingManager",
]


@dataclass
class Interval:
    """An interval of time between two times of day."""

    start: datetime.time
    """Start time of the interval."""

    end: datetime.time
    """End time of the interval."""


class IntervalRecordingManager(RecordManager):
    """A RecordManager that records during a specific interval of time."""

    def __init__(self, interval: Interval, timezone: datetime.tzinfo):
        """Initialize the IntervalRecordingManager.

        Args:
            interval: The interval of time to record during.
            timezone: The timezone to use when determining if a recording should
            be made.
        """
        self.interval = interval
        self.timezone = timezone

    def should_record(self, time: datetime.datetime) -> bool:
        """Determine if a recording should be made."""
        return self.interval.start <= time.time() <= self.interval.end


class MultiIntervalRecordingManager(RecordManager):
    """A RecordManager that records during multiple intervals of time."""

    def __init__(self, intervals: List[Interval]):
        """Initialize the MultiIntervalRecordingManager.

        Args:
            intervals: The intervals of time to record during. Should be a list
            of Interval objects.
            timezone: The timezone to use when determining if a recording
            should be made.

        """
        self.intervals = intervals
        self.timezone = timezone

    def should_record(self, time: datetime.datetime) -> bool:
        """Determine if a recording should be made."""
        return any(
            interval.start <= time.time() <= interval.end
            for interval in self.intervals
        )
