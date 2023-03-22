"""Definition of recording managers"""
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
        self.interval = interval
        self.timezone = timezone

    def should_record(self, time: datetime.time) -> bool:
        """Determine if a recording should be made"""
        return self.interval.start <= time <= self.interval.end


class MultiIntervalRecordingManager(RecordManager):
    """A RecordManager that records during multiple intervals of time."""

    def __init__(self, intervals: List[Interval], timezone: datetime.tzinfo):
        self.intervals = intervals
        self.timezone = timezone

    def should_record(self, time: datetime.time) -> bool:
        """Determine if a recording should be made"""
        return any(
            interval.start <= time <= interval.end
            for interval in self.intervals
        )
