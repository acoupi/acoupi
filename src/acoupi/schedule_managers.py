"""Definition of ScheduleManagers."""
from acoupi.types import ScheduleManager

__all__ = [
    "ConstantScheduleManager",
]


class ConstantScheduleManager(ScheduleManager):
    """Will wait for a constant amount of time between each recording."""

    def __init__(self, interval: float):
        """Initialize the schedule manager."""

        self.interval = interval
        """The interval between each recording. In seconds"""

    def time_until_next_recording(self) -> float:
        """Return the time until the next recording."""
        return self.interval
