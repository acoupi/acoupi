"""Test the recording conditions."""

import datetime

from acoupi import components, data


def test_single_interval_recording_manager(patched_now):
    """Test the interval recording manager."""
    interval = data.TimeInterval(
        start=datetime.time(10, 0),
        end=datetime.time(11, 0),
    )

    now = datetime.datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    recording_manager = components.IsInInterval(
        interval,
        timezone=datetime.timezone.utc,
    )

    patched_now(now.replace(hour=10, minute=0))
    assert recording_manager.should_record() is True

    patched_now(now.replace(hour=9, minute=59))
    assert recording_manager.should_record() is False

    patched_now(now.replace(hour=10, minute=30))
    assert recording_manager.should_record() is True

    patched_now(now.replace(hour=11, minute=0))
    assert recording_manager.should_record() is True

    patched_now(now.replace(hour=11, minute=1))
    assert recording_manager.should_record() is False


def test_multiple_interval_recording_manager(patched_now):
    """Test the multiple interval recording manager."""
    intervals = [
        data.TimeInterval(
            start=datetime.time(10, 0),
            end=datetime.time(11, 0),
        ),
        data.TimeInterval(
            start=datetime.time(12, 0),
            end=datetime.time(13, 0),
        ),
    ]

    now = datetime.datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    recording_manager = components.IsInIntervals(
        intervals,
        timezone=datetime.timezone.utc,
    )

    patched_now(now.replace(hour=9, minute=40))
    assert recording_manager.should_record() is False

    patched_now(now.replace(hour=11, minute=30))
    assert recording_manager.should_record() is False

    patched_now(now.replace(hour=10, minute=1))
    assert recording_manager.should_record() is True

    patched_now(now.replace(hour=12, minute=59))
    assert recording_manager.should_record() is True
