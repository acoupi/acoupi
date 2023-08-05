"""System functions from managing program config files.""" ""
from pathlib import Path
from typing import List, Type, TypeVar

from pydantic import BaseModel, Field

from acoupi.system.constants import PROGRAM_CONFIG_FILE, PROGRAM_PATH

__all__ = [
    "write_config",
    "load_config",
    "is_configured",
]


class CeleryConfig(BaseModel):
    """Celery config."""

    enable_utc: bool = True
    timezone: str = "UTC"
    broker_url: str = "pyamqp://guest@localhost//"
    result_backend: str = "rpc://"
    result_persistent: bool = False
    task_serializer: str = "pickle"
    result_serializer: str = "pickle"
    accept_content: List[str] = Field(default_factory=lambda: ["pickle"])


S = TypeVar("S", bound=BaseModel)


def write_config(
    config: BaseModel,
    path: Path = PROGRAM_CONFIG_FILE,
) -> None:
    """Write config to file."""
    if config is None:
        return

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    with open(path, "w") as file:
        file.write(config.model_dump_json())


def load_config(
    path: Path,
    schema: Type[S],
) -> S:
    """Load config from file."""
    with open(path) as file:
        return schema.model_validate_json(file.read())


def is_configured(
    config_file: Path = PROGRAM_CONFIG_FILE,
    program_file: Path = PROGRAM_PATH,
) -> bool:
    """Check if acoupi is configured."""
    return config_file.exists() and program_file.exists()
