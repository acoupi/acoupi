"""Pytest configuration file.

This file is automatically loaded by pytest when running tests.
It contains fixtures that are can be used in multiple test files.
"""

import datetime as dt
from pathlib import Path

import pytest

from acoupi import data
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.components.messengers import HTTPConfig
from acoupi.programs.templates import (
    AudioConfiguration,
    MessagingConfig,
    PathsConfiguration,
)
from acoupi.system import Settings
from acoupi.system.constants import CeleryConfig

pytest_plugins = ("celery.contrib.pytest",)


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
            def now(cls, *args, **kwargs):
                return time

        monkeypatch.setattr(
            "datetime.datetime",
            fake_datetime,
        )

        return time

    return set_now


@pytest.fixture
def deployment() -> data.Deployment:
    """Fixture for a deployment object."""
    return data.Deployment(name="test")


@pytest.fixture
def recording(deployment: data.Deployment) -> data.Recording:
    """Fixture for a recording object."""
    return data.Recording(
        path=Path("tests"),
        duration=1,
        samplerate=16000,
        created_on=dt.datetime.now(),
        deployment=deployment,
    )


@pytest.fixture
def model_output(recording: data.Recording) -> data.ModelOutput:
    return data.ModelOutput(
        name_model="test_model",
        recording=recording,
        tags=[
            data.PredictedTag(
                tag=data.Tag(key="test", value="value1"),
                confidence_score=0.8,
            ),
            data.PredictedTag(
                tag=data.Tag(key="test", value="value2"),
                confidence_score=0.8,
            ),
        ],
        detections=[
            data.Detection(
                location=data.BoundingBox(coordinates=(1, 1000, 2, 2000)),
                detection_score=0.6,
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="test2", value="value3"),
                        confidence_score=0.3,
                    ),
                    data.PredictedTag(
                        tag=data.Tag(key="test", value="value1"),
                        confidence_score=0.2,
                    ),
                ],
            )
        ],
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
        deployment_file=home / "config" / "deployment.json",
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


@pytest.fixture(scope="session")
def celery_config():
    return CeleryConfig().model_dump()


@pytest.fixture(scope="session")
def celery_worker_parameters():
    """Redefine this fixture to change the init parameters of Celery workers.

    This can be used e. g. to define queues the worker will consume tasks from.

    The dict returned by your fixture will then be used
    as parameters when instantiating :class:`~celery.worker.WorkController`.
    """
    return {
        "loglevel": "WARN",
    }


@pytest.fixture
def data_config(tmp_path: Path) -> PathsConfiguration:
    return PathsConfiguration(
        tmp_audio=tmp_path / "tmp",
        recordings=tmp_path / "audio",
        db_metadata=tmp_path / "metadata.db",
    )


@pytest.fixture
def audio_config() -> AudioConfiguration:
    return AudioConfiguration(duration=1, interval=2)


@pytest.fixture
def microphone_config():
    return MicrophoneConfig(
        samplerate=44100,
        audio_channels=1,
        device_name="default",
    )


@pytest.fixture
def messaging_config(tmp_path: Path) -> MessagingConfig:
    return MessagingConfig(
        messages_db=tmp_path / "messages.db",
        http=HTTPConfig(
            base_url="http://localhost:8000",
        ),
    )
