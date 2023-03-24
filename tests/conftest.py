"""Pytest configuration file.

This file is automatically loaded by pytest when running tests.
It contains fixtures that are can be used in multiple test files.
"""
import pytest
import datetime as dt


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
        "acoupi.utils.get_rpi_serial_number",
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
