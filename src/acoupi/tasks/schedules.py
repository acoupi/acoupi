"""Custom Celery schedules used by Acoupi tasks."""

from __future__ import annotations

import datetime

from celery.schedules import BaseSchedule, schedstate

__all__ = ["aligned_schedule"]


class aligned_schedule(BaseSchedule):
    """Run tasks on absolute clock boundaries at a fixed interval.

    This behaves like an interval schedule, but aligns executions to wall clock
    boundaries instead of anchoring them to the previous run time. For example,
    a ``run_every`` of 10 seconds with ``offset_seconds=0`` will run at seconds
    ``0, 10, 20, 30, 40, 50`` of every minute.
    """

    def __init__(
        self,
        run_every: datetime.timedelta,
        offset_seconds: int = 0,
        nowfun=None,
        app=None,
    ):
        """Initialise a wall-clock-aligned interval schedule.

        Parameters
        ----------
        run_every : datetime.timedelta
            Interval between valid schedule slots.
        offset_seconds : int, optional
            Offset applied within each interval. With ``run_every=10`` seconds
            and ``offset_seconds=5``, the schedule runs at ``:05, :15, :25``
            and so on. Must be non-negative and smaller than ``run_every``.
        nowfun : callable, optional
            Override used by Celery to obtain the current time. Primarily
            useful for testing.
        app : celery.Celery, optional
            Celery application instance passed through to ``BaseSchedule``.
        """
        self.run_every = run_every
        self.offset_seconds = offset_seconds
        super().__init__(nowfun=nowfun, app=app)

        interval_seconds = self.seconds
        if interval_seconds <= 0:
            raise ValueError("run_every must be greater than zero")

        if offset_seconds < 0:
            raise ValueError("offset_seconds must be non-negative")

        if offset_seconds >= interval_seconds:
            raise ValueError("offset_seconds must be smaller than run_every")

    def is_due(self, last_run_at: datetime.datetime):
        last_run_at = self.maybe_make_aware(last_run_at)
        now = self.maybe_make_aware(self.now())

        current_slot = self._slot_index(now)
        last_slot = self._slot_index(last_run_at)

        if current_slot > last_slot:
            return schedstate(is_due=True, next=self.seconds)

        return schedstate(
            is_due=False, next=self._seconds_until_next_slot(now)
        )

    def __repr__(self) -> str:
        return (
            "<clock-aligned schedule: "
            f"every {self.run_every}, offset {self.offset_seconds}s>"
        )

    @property
    def seconds(self) -> float:
        return self.run_every.total_seconds()

    def _slot_index(self, moment: datetime.datetime) -> int:
        return int((moment.timestamp() - self.offset_seconds) // self.seconds)

    def _seconds_until_next_slot(self, now: datetime.datetime) -> float:
        next_slot = (
            self._slot_index(now) + 1
        ) * self.seconds + self.offset_seconds
        return max(next_slot - now.timestamp(), 0)
