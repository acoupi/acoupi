import subprocess
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from acoupi.system.datetime import get_system_timezone, set_system_timezone


class TestGetSystemTimezone:
    def test_returns_timezone_info(self, mocker):
        mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
        mock_run.return_value = Mock(stdout="Europe/London\n")
        assert get_system_timezone() == ZoneInfo("Europe/London")
        mock_run.assert_called_once_with(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            capture_output=True,
            text=True,
            check=True,
        )

    def test_returns_none_when_command_fails(self, mocker):
        mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "timedatectl")
        assert get_system_timezone() is None


class TestSetSystemTimezone:
    def test_successfully_updates_system_timezone(self, mocker):
        mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
        assert set_system_timezone("Europe/London") is True
        mock_run.assert_called_once_with(
            ["sudo", "timedatectl", "set-timezone", "Europe/London"],
            check=True,
            capture_output=True,
        )

    def test_returns_false_when_timezone_is_invalid(self, mocker):
        mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
        assert set_system_timezone("Invalid/Timezone") is False
        mock_run.assert_not_called()

    def test_returns_false_when_command_fails(self, mocker):
        mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "sudo")
        assert set_system_timezone("Europe/London") is False
