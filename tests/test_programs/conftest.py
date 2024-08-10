import pytest

from acoupi.system.constants import CeleryConfig


@pytest.fixture(scope="session")
def celery_config():
    return CeleryConfig().model_dump()
