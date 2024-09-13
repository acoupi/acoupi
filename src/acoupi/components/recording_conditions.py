"""Recording conditions for acoupi.

Recording conditions are used to determine if a recording should be made according
to a specific condition. This is useful for example if you want to only record during
specific times of day, such as between 8am and 5pm, or if you want to record
during specific days of the week, such as only on weekdays, or if you want to record
based on the value of a sensor (e.g., readings from temperature or luminosity sensors).

Recording conditions are implemented as classes that inherit from
RecordingCondition. The class should implement the should_record method,
which returns a boolean indicating if a recording should be made.
"""

import datetime
from typing import List

from acoupi import data
from acoupi.components import types

__all__ = [
    "IsInInterval",
    "IsInIntervals",
]


class IsInInterval(types.RecordingCondition):
    """A RecordingCondition that records only during a specific interval of time.

    This class checks whether the current time falls withing a specific interval.
    If the current time is within the interval, recording is allowed.
    """

    def __init__(
        self,
        interval: data.TimeInterval,
        timezone: datetime.tzinfo,
        time: datetime.datetime,
    ):
        """Initialize the IntervalRecordingManager.

        Parameters
        ----------
        interval: data.TimeInterval
            An object containing a start and end time (datetime.time).
            The interval of time where audio recordings are allowed.
        timezone: datetime.tzinfo
            The timezone that the interval is in. This ensures that the interval is
            calculated correctly across different timezones.
        time: datetime.datetime
            The current time. Check if this time falls within the interval.
        """
        self.interval = interval
        self.timezone = timezone
        self.time = datetime.datetime

    def should_record(self) -> bool:
        """Determine if a recording should be made.

        Parameters
        ----------
        time: datetime.datetime
            The current time to check, in the same timezone as the interval.

        Returns
        -------
        bool
            True if the current time falls within the interval.
            False otherwise.

        Examples
        --------
        >>> interval = TimeInterval(start=time(8, 0), end=time(17, 0))
        >>> timezone = "Europe/London"
        >>> time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone)
        >>> IsInInterval(interval, timezone).should_record(time)
        True

        >>> interval = TimeInterval(start=time(8, 0), end=time(17, 0))
        >>> timezone = "Europe/London"
        >>> time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone)
        >>> IsInInterval(interval, timezone).should_record(time)
        False
        """
        if self.interval.start > self.interval.end:
            return (
                self.interval.start <= self.time.time()
                or self.time.time() <= self.interval.end
            )
        return self.interval.start <= self.time.time() <= self.interval.end


class IsInIntervals(types.RecordingCondition):
    """A RecordManager that records during multiple intervals of time."""

    def __init__(
        self, intervals: List[data.TimeInterval], timezone: datetime.tzinfo, time: datetime.datetime, 
    ):
        """Initialize the MultiIntervalRecordingManager.

        Args:
            intervals: The intervals of time to record during. Should be a list
                of Interval objects.
            timezone: The timezone to use when determining if a recording
                should be made.

        """
        self.intervals = intervals
        self.timezone = timezone
        self.time = datetime.datetime

    def should_record(self) -> bool:
        """Determine if a recording should be made."""
        return any(
            interval.start <= self.time.time() <= interval.end
            for interval in self.intervals
        )
