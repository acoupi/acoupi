"""System functions for managing celery apps."""
from pathlib import Path

from celery import Celery

from acoupi.system.configs import load_config
from acoupi.system.constants import CONFIG_PATH
from acoupi.system.programs import load_program


def get_celery_app(
    program_name: str,
    config_file: Path = CONFIG_PATH,
) -> Celery:
    """Get the currently setup celery app."""
    program_class = load_program(program_name)
    config_schema = program_class.get_config_schema()
    config = load_config(config_file, config_schema)
    program = program_class(config)
    return program.app
