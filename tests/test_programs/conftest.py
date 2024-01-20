import pytest

from acoupi.system.configs import CeleryConfig


@pytest.fixture(scope="session")
def celery_config():
    return CeleryConfig().model_dump()
