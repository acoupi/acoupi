"""System functions from managing program config files.""" ""
from pathlib import Path
from typing import Type, TypeVar

from acoupi import config_schemas
from acoupi.system.constants import CONFIG_PATH, PROGRAM_PATH

__all__ = [
    "write_config",
    "load_config",
    "is_configured",
]


S = TypeVar("S", bound=config_schemas.BaseConfigSchema)


def write_config(
    config: config_schemas.BaseConfigSchema,
    config_file: Path = CONFIG_PATH,
) -> None:
    """Write config to file."""
    if not config_file.parent.exists():
        config_file.parent.mkdir(parents=True)

    config.write(config_file)


def load_config(
    path: Path,
    schema: Type[S],
) -> S:
    """Load config from file."""
    return schema.from_file(path)


def is_configured(
    config_file: Path = CONFIG_PATH,
    program_file: Path = PROGRAM_PATH,
) -> bool:
    """Check if acoupi is configured."""
    return config_file.exists() and program_file.exists()
