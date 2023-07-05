"""Test the recording conditions."""

import datetime

from acoupi import components, data


def test_interval_recording_manager_is_inclusive():
    """Test the interval recording manager."""
    interval = data.TimeInterval(
        start=datetime.time(10, 0),
        end=datetime.time(11, 0),
    )

    recording_manager = components.IsInInterval(
        interval,
        timezone=datetime.timezone.utc,
    )

    now = datetime.datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    assert (
        recording_manager.should_record(now.replace(hour=9, minute=59))
        is False
    )
    assert (
        recording_manager.should_record(now.replace(hour=10, minute=0)) is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=10, minute=30))
        is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=11, minute=0)) is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=11, minute=1))
        is False
    )


def test_multiple_interval_recording_manager():
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

    recording_manager = components.IsInIntervals(
        intervals,
        timezone=datetime.timezone.utc,
    )

    now = datetime.datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    assert (
        recording_manager.should_record(now.replace(hour=9, minute=59))
        is False
    )
    assert (
        recording_manager.should_record(now.replace(hour=10, minute=0)) is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=10, minute=30))
        is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=11, minute=0)) is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=11, minute=1))
        is False
    )
    assert (
        recording_manager.should_record(now.replace(hour=12, minute=0)) is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=12, minute=30))
        is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=13, minute=0)) is True
    )
    assert (
        recording_manager.should_record(now.replace(hour=13, minute=1))
        is False
    )
