"""Test acoupi schedule managers."""
from acoupi import schedule_managers


def test_constant_schedule_manager():
    """Test constant schedule manager."""
    manager = schedule_managers.ConstantScheduleManager(1)
    assert manager.time_until_next_recording() == 1

    manager = schedule_managers.ConstantScheduleManager(2)
    assert manager.time_until_next_recording() == 2
