"""System functions from managing program config files.""" ""
import json
from pathlib import Path
from typing import List, Type, TypeVar

from pydantic import BaseModel, Field

from acoupi.system.constants import Settings

__all__ = [
    "write_config",
    "load_config",
    "is_configured",
    "show_config",
    "get_config_value",
    "sub_config_value",
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
    path: Path,
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


def is_configured(settings: Settings) -> bool:
    """Check if acoupi is configured."""
    return (
        settings.program_config_file.exists()
        and settings.program_file.exists()
        and settings.program_name_file.exists()
    )


def show_config(settings: Settings) -> dict:
    """Show acoupi config file."""
    with open(settings.program_config_file) as file:
        return json.load(file)


def get_config_value(config_value: str, settings: Settings):
    """Get a specific configuration value of acoupi."""
    config = show_config(settings)
    return config[config_value]


def sub_config_value(
    config_param_name: str,
    new_config_value: Type[S],
    settings: Settings,
):
    """Substitute a specific configuration value of acoupi."""
    config_file_path = settings.program_config_file
    with open(config_file_path) as file:
        config_data = json.load(file)
        config_data[config_param_name] = new_config_value

    with open(config_file_path, "w") as file:
        return json.dump(config_data, file)
