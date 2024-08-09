"""System functions from managing program config files."""

import json
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel, Field, ValidationError

from acoupi.system import exceptions
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
    config: Optional[BaseModel],
    path: Path,
) -> None:
    """Write config to file."""
    if config is None:
        return

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    with open(path, "w") as file:
        file.write(config.model_dump_json())


def load_config(path: Path, schema: Type[S]) -> S:
    """Load config from file.

    Parameters
    ----------
    path
        Path to the config file.
    schema
        Pydantic model to validate the config.

    Returns
    -------
    S
        The loaded config.

    Raises
    ------
    ConfigurationError
        If the configuration is invalid.
    FileNotFoundError
        If the config file does not exist.
    """
    with open(path) as file:
        try:
            return schema.model_validate_json(file.read())
        except (ValueError, ValidationError) as error:
            raise exceptions.ConfigurationError(
                message=f"Invalid configuration in {path}: {error}",
                help="Check the configuration file for errors.",
            ) from error


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
    settings: Settings, config_param_name: str, new_config_value: Type[S]
):
    """Update Values in Configuration File."""
    config_schema = show_config(settings)

    if config_param_name in config_schema:
        config_schema[config_param_name] = new_config_value

    with open(settings.program_config_file, "w") as file:
        return json.dump(config_schema, file)
