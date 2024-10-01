from pathlib import Path

import pytest

from acoupi.components import MicrophoneConfig
from acoupi.programs.templates import BasicConfiguration, DataConfiguration
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
def basic_configuration(tmp_path: Path) -> BasicConfiguration:
    return BasicConfiguration(
        microphone=MicrophoneConfig(
            device_name="default",
        ),
        data=DataConfiguration(
            tmp=tmp_path / "tmp",
            audio=tmp_path / "audio",
            metadata=tmp_path / "metadata.db",
        ),
    )
