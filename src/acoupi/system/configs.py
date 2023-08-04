from pathlib import Path

from acoupi import config_schemas
from acoupi.system.constants import CONFIG_PATH, PROGRAM_PATH

__all__ = [
    "write_config",
    "is_configured",
]


def write_config(
    config: config_schemas.BaseConfigSchema,
    config_file: Path = CONFIG_PATH,
) -> None:
    """Write config to file."""
    if not config_file.parent.exists():
        config_file.parent.mkdir(parents=True)

    config.write(config_file)


def is_configured(
    config_file: Path = CONFIG_PATH,
    program_file: Path = PROGRAM_PATH,
) -> bool:
    """Check if acoupi is configured."""
    return config_file.exists() and program_file.exists()
