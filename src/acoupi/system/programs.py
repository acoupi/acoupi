"""System functions for managing Acoupi programs."""
import inspect
from importlib import import_module
from typing import List, Optional, Type

from acoupi import programs
from acoupi.system import exceptions
from acoupi.system.configs import CeleryConfig, load_config, write_config
from acoupi.system.constants import Settings
from acoupi.system.parsers import parse_config_from_args
from acoupi.system.scripts import write_scripts
from acoupi.system.services import install_services
from acoupi.system.templates import render_template

__all__ = [
    "load_program_class",
    "write_program_file",
    "setup_program",
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
    except ModuleNotFoundError:
        raise exceptions.ProgramNotFoundError(program=program)

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


def setup_program(
    settings: Settings,
    program_name: str,
    args: Optional[List[str]] = None,
    prompt: bool = False,
) -> None:
    """Setup an Acoupi Program."""
    if args is None:
        args = []

    # Load acoupi program class from specified module
    program_class = load_program_class(program_name)

    # Write the celery app program file
    write_program_file(program_name, settings)

    # Write the name of the program to a file
    if not settings.program_name_file.parent.exists():
        settings.program_name_file.parent.mkdir(parents=True)
    settings.program_name_file.write_text(program_name)

    # Get program config schema
    config_schema = program_class.get_config_schema()
    if config_schema is not None:
        # Generate program configuration from arguments
        config = parse_config_from_args(config_schema, args, prompt=prompt)

        # Write program configuration to file
        write_config(config, settings.program_config_file)

    # Generate scripts for starting, stopping, and restarting the program
    worker_config = program_class.get_worker_config()
    write_scripts(worker_config, settings)

    # Generate celery configuration from arguments and write to file
    celery_config = parse_config_from_args(CeleryConfig, args, prompt=False)
    write_config(celery_config, settings.celery_config_file)

    # Make sure run and log directories exist
    settings.run_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    # Install systemd services for acoupi
    install_services(settings)
