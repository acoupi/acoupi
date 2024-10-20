"""System functions for managing Acoupi programs."""

import inspect
import json
import warnings
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Type

from celery import Celery
from pydantic import BaseModel

from acoupi.components import types
from acoupi.components.stores import SqliteStore
from acoupi.programs.core import base as programs
from acoupi.programs.core.workers import DEFAULT_WORKER_CONFIG, WorkerConfig
from acoupi.system import exceptions
from acoupi.system.config import load_config
from acoupi.system.constants import CeleryConfig, Settings
from acoupi.system.tasks import run_task
from acoupi.system.templates import render_template

__all__ = [
    "end_program",
    "load_program",
    "load_program_class",
    "load_config_schema",
    "write_program_file",
]


def load_program_class(program_name: str) -> Type[programs.AcoupiProgram]:
    """Load the acoupi program class from a specified module.

    This function searches the given module for a valid AcoupiProgram class. If
    multiple such classes exist within the module, it prioritizes classes that
    are not further subclassed.

    Parameters
    ----------
    program_name
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
    settings
        The settings object containing the paths to the program and celery
        config files.

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
    app.config_from_object(celery_config.model_dump())
    return program_class(config, app)


def load_config_schema(settings: Settings) -> type[BaseModel]:
    """Load the configuration schema for the program."""
    program_name = settings.program_name_file.read_text().strip()
    program_class = load_program_class(program_name)
    return program_class.get_config_schema()


def load_worker_config(settings: Settings) -> WorkerConfig:
    """Load the configuration schema for the program."""
    program_name = settings.program_name_file.read_text().strip()
    program_class = load_program_class(program_name)
    return program_class.worker_config or DEFAULT_WORKER_CONFIG


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


def get_program_store(settings: Settings) -> types.Store:
    """Get the store for the program."""
    db_path = Path(
        json.load(settings.program_config_file.open())["paths"]["db_metadata"]
    )
    store = SqliteStore(db_path=db_path)
    return store


def end_program(settings: Settings) -> None:
    """End the current program.

    After stopping and disabling the systemd services, the deployment is ended.
    To ensure the correct restarting of the next program, the end_program() function
    ensure that remaining tasks are completed when the program is stopped.

    The tasks to check are:
    - file_management_task (if implemented). Check if there are remaning files in the
    temprary directory and move them to the correct directory.
    - detection_task (if implemented). Check if there are remaning files to be processed
    and process them.
    """
    tmp_audio_path = Path(
        json.load(settings.program_config_file.open())["paths"]["tmp_audio"]
    )
    recordings = list(tmp_audio_path.glob("*"))

    if len(recordings) > 0:
        print(
            f"{len(recordings)} files in the temporary directory, running file_management_task."
        )
        run_task(load_program(settings), "file_management_task")

        remaining_recordings = list(tmp_audio_path.glob("*"))
        print(
            f"Remaining files in temp_directory: {len(remaining_recordings)}. Run detection task."
        )

        if len(remaining_recordings) > 0:
            # Get data.Recording for the remaining files
            store = get_program_store(settings)
            recordings = store.get_recordings_by_path(remaining_recordings)
            for recording, _ in recordings:
                print(f"Detection running on recording: {recording.path}")
                run_task(load_program(settings), "detection_task", recording)

            run_task(load_program(settings), "file_management_task")
            check_remaining_files = list(tmp_audio_path.glob("*"))
            print(
                f"Remaining files in temp_directory: {len(check_remaining_files)}."
            )


class ProgramState(str, Enum):
    OK = "ok"
    UNHEALTHY = "unhealthy"
    ERROR = "error"


def get_program_state(settings: Settings) -> ProgramState:
    program = load_program(settings)
    try:
        program.check(program.config)
        return ProgramState.OK
    except exceptions.HealthCheckError:
        return ProgramState.UNHEALTHY
    except:  # noqa: E722
        return ProgramState.ERROR
