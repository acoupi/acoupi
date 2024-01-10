"""Pytest configuration file.

This file is automatically loaded by pytest when running tests.
It contains fixtures that are can be used in multiple test files.
"""
import datetime as dt
from pathlib import Path

import pytest

from acoupi import data
from acoupi.system import Settings


@pytest.fixture
def patched_rpi_serial_number(monkeypatch) -> str:
    """Patch the RPi serial number.

    In order to use this fixture, you must import the module that uses
    the get_rpi_serial_number function. This is because the patching
    happens at import time.

    Example:
        from acoupi import utils

        def test_foo(patched_rpi_serial_number):
            assert utils.get_rpi_serial_number() == "1234567890ABCDEF"
    """
    serial_number = "1234567890ABCDEF"
    monkeypatch.setattr(
        "acoupi.devices.get_rpi_serial_number",
        lambda: serial_number,
    )
    return serial_number


@pytest.fixture
def patched_now(monkeypatch):
    """Patch the datetime.datetime.now function.

    Example:
        def test_foo(patched_now):
            now = patched_now()
            assert datetime.datetime.now() == now

    You can also pass in a datetime.datetime object to set the time
    that is returned by the patched function.

    Example:
        def test_foo(patched_now):
            now = patched_now(datetime.datetime(2020, 1, 1))
            assert datetime.datetime.now() == now
    """
    _now = dt.datetime.now()

    def set_now(time: dt.datetime = _now):
        class fake_datetime:
            @classmethod
            def now(cls):
                return time

        monkeypatch.setattr(
            "datetime.datetime",
            fake_datetime,
        )

        return time

    return set_now


@pytest.fixture
def deployment():
    """Fixture for a deployment object."""
    return data.Deployment(name="test")


@pytest.fixture
def recording(deployment: data.Deployment):
    """Fixture for a recording object."""
    return data.Recording(
        path=Path("tests"),
        duration=1,
        samplerate=16000,
        datetime=dt.datetime.now(),
        deployment=deployment,
    )


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Fixture for a settings object."""
    home = tmp_path / ".acoupi"
    home.mkdir(exist_ok=True)
    return Settings(
        home=home,
        app_name="app",
        program_file=home / "app.py",
        program_name_file=home / "config" / "name",
        program_config_file=home / "config" / "program.json",
        celery_config_file=home / "config" / "celery.json",
        env_file=home / "config" / "env",
        run_dir=home / "run",
        log_dir=home / "log",
        log_level="INFO",
        start_script_path=home / "bin" / "acoupi-workers-start.sh",
        stop_script_path=home / "bin" / "acoupi-workers-stop.sh",
        restart_script_path=home / "bin" / "acoupi-workers-restart.sh",
        beat_script_path=home / "bin" / "acoupi-beat.sh",
        acoupi_service_file="acoupi.service",
        acoupi_beat_service_file="acoupi-beat.service",
    )
