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

from astral import LocationInfo
from astral.sun import sun

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
        """
        self.interval = interval
        self.timezone = timezone

    def should_record(self) -> bool:
        """Determine if a recording should be made.

        Returns
        -------
        bool
            True if the current time falls within the interval.
            False otherwise.

        Notes
        -----
        Uses the current time as provided by the system clock.

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
        now = datetime.datetime.now(tz=self.timezone).time()

        if self.interval.start > self.interval.end:
            return self.interval.start <= now or now <= self.interval.end
        return self.interval.start <= now <= self.interval.end


class IsInIntervals(types.RecordingCondition):
    """A RecordManager that records during multiple intervals of time."""

    def __init__(
        self,
        intervals: List[data.TimeInterval],
        timezone: datetime.tzinfo,
    ):
        """Initialize the MultiIntervalRecordingManager.

        Parameters
        ----------
        intervals: The intervals of time to record during. Should be a list
            of Interval objects.
        timezone: The timezone to use when determining if a recording
            should be made.

        """
        self.intervals = intervals
        self.timezone = timezone

    def should_record(self) -> bool:
        """Determine if a recording should be made."""
        now = datetime.datetime.now(tz=self.timezone).time()
        return any(
            interval.start <= now <= interval.end
            for interval in self.intervals
        )


class DawnTimeInterval(types.RecordingCondition):
    """A RecordingCondition that records only during the dawn time interval."""

    duration: float
    """The duration of time (in minutes) before and after dawntime."""

    timezone: datetime.tzinfo
    """The timezone that the dawn time is in."""

    def __init__(self, duration: float, timezone: datetime.tzinfo):
        """Initialize the DawnTimeInterval.

        Parameters
        ----------
        duration: float
            The duration of time (in minutes) before and after dawntime.
        timezone: datetime.tzinfo
            The timezone that the dawn time is in.
        """
        self.duration = duration
        self.timezone = timezone

    def should_record(self) -> bool:
        """Determine if a recording should be made.

        Returns
        -------
        bool
            True if the current time is within the dawn time interval.
            False otherwise.

        Examples
        --------
        >>> dawn_time = time(6, 0)
        >>> duration = 30
        >>> timezone = "Europe/London"
        >>> time = datetime(2024, 1, 1, 6, 15, 0, tzinfo=timezone)
        >>> DawnTimeInterval(
        ...     dawn_time, duration, timezone
        ... ).should_record(time)
        True

        >>> dawn_time = time(6, 0)
        >>> duration = 30
        >>> timezone = "Europe/London"
        >>> time = datetime(2024, 1, 1, 5, 45, 0, tzinfo=timezone)
        >>> DawnTimeInterval(
        ...     dawn_time, duration, timezone
        ... ).should_record(time)
        False
        """
        now = datetime.datetime.now(self.timezone)
        sun_info = sun(
            LocationInfo(str(self.timezone)).observer,
            date=now.astimezone(self.timezone),
            tzinfo=self.timezone,
        )
        dawntime = sun_info["dawn"]
        start_dawninterval = dawntime - datetime.timedelta(
            minutes=self.duration
        )
        end_dawninterval = dawntime + datetime.timedelta(minutes=self.duration)

        return (
            start_dawninterval.time() <= now.time() <= end_dawninterval.time()
        )
