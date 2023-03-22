"""Test the recording managers."""

from datetime import time, timezone

from acoupi.recording_managers import Interval, IntervalRecordingManager


def test_interval_recording_manager_is_inclusive():
    """Test the interval recording manager."""
    interval = Interval(start=time(10, 0), end=time(11, 0))

    recording_manager = IntervalRecordingManager(
        interval,
        timezone=timezone.utc,
    )

    assert recording_manager.should_record(time(9, 59)) is False
    assert recording_manager.should_record(time(10, 0)) is True
    assert recording_manager.should_record(time(10, 30)) is True
    assert recording_manager.should_record(time(11, 0)) is True
    assert recording_manager.should_record(time(11, 1)) is False
