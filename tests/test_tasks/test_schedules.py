import datetime

import pytest

from acoupi.tasks.schedules import aligned_schedule

UTC = datetime.timezone.utc


def test_aligned_schedule_is_due_on_interval_boundary():
    schedule = aligned_schedule(
        run_every=datetime.timedelta(seconds=10),
        nowfun=lambda: datetime.datetime(2024, 1, 1, 12, 0, 20, tzinfo=UTC),
    )

    state = schedule.is_due(
        last_run_at=datetime.datetime(2024, 1, 1, 12, 0, 19, tzinfo=UTC)
    )

    assert state.is_due is True
    assert state.next == 10


def test_aligned_schedule_waits_until_next_boundary():
    schedule = aligned_schedule(
        run_every=datetime.timedelta(seconds=10),
        nowfun=lambda: datetime.datetime(2024, 1, 1, 12, 0, 12, tzinfo=UTC),
    )

    state = schedule.is_due(
        last_run_at=datetime.datetime(2024, 1, 1, 12, 0, 10, tzinfo=UTC)
    )

    assert state.is_due is False
    assert state.next == pytest.approx(8)


def test_aligned_schedule_honours_offset_seconds():
    schedule = aligned_schedule(
        run_every=datetime.timedelta(seconds=10),
        offset_seconds=5,
        nowfun=lambda: datetime.datetime(2024, 1, 1, 12, 0, 25, tzinfo=UTC),
    )

    state = schedule.is_due(
        last_run_at=datetime.datetime(2024, 1, 1, 12, 0, 24, tzinfo=UTC)
    )

    assert state.is_due is True
    assert state.next == 10


def test_aligned_schedule_does_not_repeat_in_same_slot():
    schedule = aligned_schedule(
        run_every=datetime.timedelta(seconds=10),
        nowfun=lambda: datetime.datetime(
            2024, 1, 1, 12, 0, 20, 500000, tzinfo=UTC
        ),
    )

    state = schedule.is_due(
        last_run_at=datetime.datetime(2024, 1, 1, 12, 0, 20, tzinfo=UTC)
    )

    assert state.is_due is False
    assert state.next == pytest.approx(9.5)


def test_aligned_schedule_rejects_invalid_offset():
    with pytest.raises(
        ValueError, match="offset_seconds must be smaller than run_every"
    ):
        aligned_schedule(
            run_every=datetime.timedelta(seconds=10),
            offset_seconds=10,
        )
