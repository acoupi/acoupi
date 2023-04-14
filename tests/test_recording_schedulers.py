"""Test acoupi recording schedulers."""
from acoupi import recording_schedulers


def test_constant_schedule_manager():
    """Test constant schedule manager."""
    manager = recording_schedulers.IntervalScheduler(1)
    assert manager.time_until_next_recording() == 1

    manager = recording_schedulers.IntervalScheduler(2)
    assert manager.time_until_next_recording() == 2
