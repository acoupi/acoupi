"""System functions for managing Acoupi programs."""
import inspect
from importlib import import_module
from pathlib import Path
from typing import List, Optional, Type

from acoupi import programs
from acoupi.system import constants
from acoupi.system.configs import CeleryConfig, write_config
from acoupi.system.constants import PROGRAM_CONFIG_FILE, PROGRAM_PATH
from acoupi.system.parsers import parse_config_from_args
from acoupi.system.scripts import write_scripts
from acoupi.system.services import install_services
from acoupi.system.templates import render_template

__all__ = [
    "load_program",
    "write_program_file",
]


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


def write_program_file(
    program_name: str,
    config_file: Path = PROGRAM_CONFIG_FILE,
    path: Path = PROGRAM_PATH,
) -> None:
    """Write the python script with the celery app to run."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "app.py.jinja2",
            program_name=program_name,
            config_file=config_file,
        )
    )


def setup_program(
    program_name: str,
    args: Optional[List[str]] = None,
    program_config_file: Path = constants.PROGRAM_CONFIG_FILE,
    program_file: Path = constants.PROGRAM_PATH,
    celery_config_file: Path = constants.CELERY_CONFIG_PATH,
    start_script: Path = constants.START_SCRIPT_PATH,
    stop_script: Path = constants.STOP_SCRIPT_PATH,
    restart_script: Path = constants.RESTART_SCRIPT_PATH,
    beat_script: Path = constants.BEAT_SCRIPT_PATH,
    run_dir: Path = constants.RUN_DIR,
    log_dir: Path = constants.LOG_DIR,
    log_level: str = constants.LOG_LEVEL,
    app_name: str = constants.APP_NAME,
    prompt: bool = False,
) -> None:
    """Setup an Acoupi Program."""
    if args is None:
        args = []

    # Load acoupi program class from specified module
    program_class = load_program(program_name)

    # Write the celery app program file
    write_program_file(
        program_name,
        config_file=program_config_file,
        path=program_file,
    )

    # Get program config schema
    config_schema = program_class.get_config_schema()
    if config_schema is not None:
        # Generate program configuration from arguments
        config = parse_config_from_args(config_schema, args, prompt=prompt)

        # Write program configuration to file
        write_config(
            config,
            path=program_config_file,
        )

    # Generate scripts for starting, stopping, and restarting the program
    worker_config = program_class.get_worker_config()
    write_scripts(
        worker_config,
        start_path=start_script,
        stop_path=stop_script,
        restart_path=restart_script,
        app_name=app_name,
        log_level=log_level,
        log_dir=log_dir,
        run_dir=run_dir,
    )

    # Generate celery configuration from arguments and write to file
    celery_config = parse_config_from_args(CeleryConfig, args, prompt=False)
    write_config(
        path=celery_config_file,
        config=celery_config,
    )

    # Make sure run and log directories exist
    run_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Install systemd services for acoupi
    install_services(
        environment_file=celery_config_file,
        working_directory=program_file.parent,
        start_script=start_script,
        stop_script=stop_script,
        restart_script=restart_script,
        beat_script=beat_script,
    )
