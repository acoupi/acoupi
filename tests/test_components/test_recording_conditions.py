"""Test the recording conditions."""

import collections
import datetime

from acoupi import components, data
from acoupi.components.recording_conditions import HasSufficientSpace


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


class TestHasSufficientSpace:
    def test_space_true(self, mocker):
        usage = collections.namedtuple("usage", ["total", "used", "free"])
        mocker.patch(
            "acoupi.components.recording_conditions.shutil.disk_usage",
            return_value=usage(total=10, used=4, free=1_000_001),
        )

        condition = HasSufficientSpace(min_space=1, unit="MB")

        assert condition.should_record() is True

    def test_space_false(self, mocker):
        usage = collections.namedtuple("usage", ["total", "used", "free"])
        mocker.patch(
            "acoupi.components.recording_conditions.shutil.disk_usage",
            return_value=usage(total=10, used=4, free=999_999),
        )

        condition = HasSufficientSpace(min_space=1, unit="MB")

        assert condition.should_record() is False

    def test_space_binary(self, mocker):
        usage = collections.namedtuple("usage", ["total", "used", "free"])
        mocker.patch(
            "acoupi.components.recording_conditions.shutil.disk_usage",
            return_value=usage(total=10, used=4, free=1_048_577),
        )

        condition = HasSufficientSpace(min_space=1, unit="MB", binary=True)

        assert condition.should_record() is True
