"""System functions for managing Acoupi programs."""

import inspect
from importlib import import_module
from typing import Type

from acoupi import programs
from acoupi.system import exceptions
from acoupi.system.configs import CeleryConfig, load_config
from acoupi.system.constants import Settings
from acoupi.system.templates import render_template

__all__ = [
    "load_program",
    "load_program_class",
    "write_program_file",
]


def load_program_class(program: str) -> Type[programs.AcoupiProgram]:
    """Load the acoupi program class from a specified module.

    Parameters
    ----------
    program
        The name of the module containing the acoupi program class.

    Returns
    -------
    Type[programs.AcoupiProgram]
        The acoupi program class.

    Raises
    ------
    exceptions.ProgramNotFoundError
        If the specified program module is not found.
    exceptions.InvalidProgramError
        If the loaded class is not a valid acoupi program class.
    """
    try:
        program_module = import_module(program)
    except ModuleNotFoundError as e:
        raise exceptions.ProgramNotFoundError(program=program) from e

    for _, class_ in inspect.getmembers(program_module, inspect.isclass):
        if (
            issubclass(class_, programs.AcoupiProgram)
            and not class_ == programs.AcoupiProgram
        ):
            return class_

    raise exceptions.InvalidProgramError(program=program)


def load_program(settings: Settings) -> programs.AcoupiProgram:
    """Load a fully configured acoupi program.

    This function loads the acoupi program class from the specified module,
    instantiates it, and configures it with the specified config files.

    Parameters
    ----------
    program_name_file
        Path to the file containing the program name. Defaults to
        PROGRAM_NAME_FILE.
    config_file
        Path to the configuration file for the acoupi program. Defaults to
        PROGRAM_CONFIG_FILE.
    celery_config_file
        Path to the Celery configuration file. Defaults to CELERY_CONFIG_PATH.

    Returns
    -------
    programs.AcoupiProgram
        A fully configured instance of the acoupi program class.

    Raises
    ------
    exceptions.ProgramNotFoundError
        If the program module is not found.
    exceptions.InvalidProgramError
        If the loaded class is not a valid acoupi program class.
    """
    program_name = settings.program_name_file.read_text().strip()
    program_class = load_program_class(program_name)
    config_schema = program_class.get_config_schema()
    if config_schema is not None:
        config = load_config(settings.program_config_file, config_schema)
    else:
        config = None
    celery_config = load_config(settings.celery_config_file, CeleryConfig)
    return program_class(config, celery_config)


def write_program_file(
    program_name: str,
    settings: Settings,
) -> None:
    """Write the python script with the celery app to run."""
    path = settings.program_file

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "app.py.jinja2",
            program_name=program_name,
            settings=settings,
        )
    )
