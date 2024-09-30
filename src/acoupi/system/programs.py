"""System functions for managing Acoupi programs."""

import inspect
import warnings
from importlib import import_module
from typing import Type

from celery import Celery

from acoupi.programs.core import base as programs
from acoupi.system import exceptions
from acoupi.system.config import load_config
from acoupi.system.constants import CeleryConfig, Settings
from acoupi.system.templates import render_template

__all__ = [
    "load_program",
    "load_program_class",
    "write_program_file",
]


def load_program_class(program_name: str) -> Type[programs.AcoupiProgram]:
    """Load the acoupi program class from a specified module.

    This function searches the given module for a valid AcoupiProgram class. If
    multiple such classes exist within the module, it prioritizes classes that
    are not further subclassed.

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

    Notes
    -----
    When multiple AcoupiProgram classes are found within the module, this
    function will attempt to select one that is not further subclassed. If
    multiple such "final" classes exist, a warning will be issued, and the
    first one encountered will be selected. It is recommended that when
    exposing AcoupiProgram classes in a module, only one "final"
    (non-subclassable) class be made available.
    """
    try:
        program_module = import_module(program_name)
    except ModuleNotFoundError as e:
        raise exceptions.ProgramNotFoundError(program=program_name) from e

    def is_acoupi_program_class(cls):
        return (
            inspect.isclass(cls)
            and not inspect.isabstract(cls)
            and issubclass(cls, programs.AcoupiProgram)
        )

    all_programs = inspect.getmembers(program_module, is_acoupi_program_class)

    if not all_programs:
        raise exceptions.ProgramNotFoundError(program=program_name)

    valid_classes = dict(all_programs)

    for _, class_ in all_programs:
        assert issubclass(class_, programs.AcoupiProgram)

        for base_class in class_.__bases__:
            base_name = base_class.__name__
            valid_classes.pop(base_name, None)

    if len(valid_classes) > 1:
        warnings.warn(
            f"Found multiple programs in {program_name}. "
            "Imported the first one but this may not be the desired behavior.",
            stacklevel=1,
        )

    if valid_classes:
        return valid_classes.popitem()[1]

    raise exceptions.InvalidProgramError(program=program_name)


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
    app = Celery()
    app.config_from_object(celery_config)

    return program_class(config, app)


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
