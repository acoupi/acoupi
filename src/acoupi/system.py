"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""
import datetime
import inspect
import os
from importlib import import_module
from pathlib import Path
from typing import Type

from celery import Celery

from acoupi import config_schemas, data, programs

__all__ = [
    "load_program",
    "get_celery_app",
]


ACOUPI_HOME = Path(os.environ.get("ACOUPI_HOME", str(Path.home() / ".acoupi")))

PROGRAM_PATH = ACOUPI_HOME / "app.py"
CONFIG_PATH = ACOUPI_HOME / "config.json"

PROGRAM_TEMPLATE = """
from acoupi.system import get_celery_app

app = get_celery_app(
    program_name="{program_name}",
    config_file="{config_file}",
)
"""


def get_current_deployment() -> data.Deployment:
    """Get current deployment."""
    # TODO: implement this better
    return data.Deployment(
        name="default",
        started_on=datetime.datetime.now(),
    )


def load_program(program: str) -> Type[programs.AcoupiProgram]:
    """Load acoupi program from path."""
    program_module = import_module(program)

    for _, class_ in inspect.getmembers(program_module, inspect.isclass):
        if (
            issubclass(class_, programs.AcoupiProgram)
            and not class_ == programs.AcoupiProgram
        ):
            return class_

    raise ValueError(f"program {program} not found")


def write_config(
    config: config_schemas.BaseConfigSchema,
    config_file: Path = CONFIG_PATH,
) -> None:
    """Write config to file."""
    if not config_file.parent.exists():
        config_file.parent.mkdir(parents=True)

    config.write(config_file)


def write_program_file(
    program_name: str,
    config_file: Path = CONFIG_PATH,
    program_file: Path = PROGRAM_PATH,
) -> None:
    """Write the python script with the celery app to run."""
    if not program_file.parent.exists():
        program_file.parent.mkdir(parents=True)

    with open(program_file, "w") as file:
        file.write(
            PROGRAM_TEMPLATE.format(
                program_name=program_name,
                config_file=config_file,
            )
        )


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


def is_configured(
    config_file: Path = CONFIG_PATH,
    program_file: Path = PROGRAM_PATH,
) -> bool:
    """Check if acoupi is configured."""
    return config_file.exists() and program_file.exists()
