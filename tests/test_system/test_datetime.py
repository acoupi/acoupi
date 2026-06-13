import subprocess
from unittest.mock import Mock

from acoupi.system.datetime import get_system_timezone, set_system_timezone


def test_get_system_timezone(mocker):
    mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
    mock_run.return_value = Mock(stdout="Europe/London\n")
    assert get_system_timezone() == "Europe/London"
    mock_run.assert_called_once_with(
        ["timedatectl", "show", "--property=Timezone", "--value"],
        capture_output=True,
        text=True,
        check=True,
    )


def test_get_system_timezone_fails(mocker):
    mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
    mock_run.side_effect = subprocess.CalledProcessError(1, "timedatectl")
    assert get_system_timezone() is None


def test_set_system_timezone(mocker):
    mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
    assert set_system_timezone("Europe/London") is True
    mock_run.assert_called_once_with(
        ["sudo", "timedatectl", "set-timezone", "Europe/London"],
        check=True,
        capture_output=True,
    )


def test_set_system_timezone_invalid_tz(mocker):
    mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
    assert set_system_timezone("Invalid/Timezone") is False
    mock_run.assert_not_called()


def test_set_system_timezone_fails(mocker):
    mock_run = mocker.patch("acoupi.system.datetime.subprocess.run")
    mock_run.side_effect = subprocess.CalledProcessError(1, "sudo")
    assert set_system_timezone("Europe/London") is False
