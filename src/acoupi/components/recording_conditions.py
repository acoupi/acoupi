"""Recording conditions for acoupi.

Recording conditions are used to determine if a recording should be made at a
specific time. This is useful for example if you want to only record during
specific times of day, such as between 8am and 5pm, or if you want to record
during specific days of the week, such as only on weekdays.

Recording conditions are implemented as classes that inherit from
RecordingCondition. The class should implement the should_record method,
which takes a datetime.datetime object and returns a boolean indicating if a
recording should be made at that time.
"""
import datetime
from typing import List

from acoupi.components.types import RecordingCondition
from acoupi.data import TimeInterval

__all__ = [
    "IsInInterval",
    "IsInIntervals",
]


class IsInInterval(RecordingCondition):
    """A RecordManager that records during a specific interval of time."""

    def __init__(self, interval: TimeInterval, timezone: datetime.tzinfo):
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


class IsInIntervals(RecordingCondition):
    """A RecordManager that records during multiple intervals of time."""

    def __init__(self, intervals: List[TimeInterval], timezone: datetime.tzinfo):
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
