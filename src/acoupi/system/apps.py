"""System functions for managing celery apps."""
from pathlib import Path

from celery import Celery

from acoupi.system.configs import CeleryConfig, load_config
from acoupi.system.constants import CELERY_CONFIG_PATH, PROGRAM_CONFIG_FILE
from acoupi.system.programs import load_program

__all__ = [
    "get_celery_app",
]


def get_celery_app(
    program_name: str,
    config_file: Path = PROGRAM_CONFIG_FILE,
    celery_config_file: Path = CELERY_CONFIG_PATH,
) -> Celery:
    """Get the currently setup celery app."""
    program_class = load_program(program_name)
    config_schema = program_class.get_config_schema()
    if config_schema is not None:
        config = load_config(config_file, config_schema)
    else:
        config = None
    celery_config = load_config(celery_config_file, CeleryConfig)
    program = program_class(config, celery_config)
    return program.app
