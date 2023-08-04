"""System functions from managing program config files.""" ""
from pathlib import Path
from typing import Type, TypeVar

from acoupi.programs.configs import BaseConfigSchema
from acoupi.system.constants import PROGRAM_CONFIG_FILE, PROGRAM_PATH

__all__ = [
    "write_config",
    "load_config",
    "is_configured",
]


S = TypeVar("S", bound=BaseConfigSchema)


def write_config(
    config: BaseConfigSchema,
    path: Path = PROGRAM_CONFIG_FILE,
) -> None:
    """Write config to file."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    config.write(path)


def load_config(
    path: Path,
    schema: Type[S],
) -> S:
    """Load config from file."""
    return schema.from_file(path)


def is_configured(
    config_file: Path = PROGRAM_CONFIG_FILE,
    program_file: Path = PROGRAM_PATH,
) -> bool:
    """Check if acoupi is configured."""
    return config_file.exists() and program_file.exists()
