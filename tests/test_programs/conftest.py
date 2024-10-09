from pathlib import Path

import pytest

from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.components.messengers import HTTPConfig
from acoupi.programs.templates import (
    AudioConfiguration,
    MessagingConfig,
    PathsConfiguration,
)
from acoupi.system.constants import CeleryConfig


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
def paths_config(tmp_path: Path) -> PathsConfiguration:
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
