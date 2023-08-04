from pathlib import Path

from celery import Celery

from acoupi.system.constants import CONFIG_PATH
from acoupi.system.programs import load_program


def get_celery_app(
    program_name: str,
    config_file: Path = CONFIG_PATH,
) -> Celery:
    """Get the currently setup celery app."""
    program_class = load_program(program_name)
    config_schema = program_class.get_config_schema()
    config = config_schema.from_file(config_file)
    program = program_class(config)
    return program.app
