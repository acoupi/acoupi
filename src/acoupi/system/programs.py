"""System functions for managing Acoupi programs."""
import inspect
from importlib import import_module
from pathlib import Path
from typing import List, Optional, Type

from acoupi import programs
from acoupi.system.services import install_services
from acoupi.system import constants
from acoupi.system.celery import write_beat_script, write_celery_config
from acoupi.system.configs import write_config
from acoupi.system.constants import PROGRAM_CONFIG_FILE, PROGRAM_PATH
from acoupi.system.templates import render_template
from acoupi.system.workers import write_workers_scripts

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
) -> None:
    """Setup an Acoupi Program."""
    if args is None:
        args = []

    program_class = load_program(program_name)
    config_schema = program_class.get_config_schema()
    config = config_schema.from_args(args)
    worker_config = program_class.get_worker_config()

    write_config(
        config,
        path=program_config_file,
    )
    write_program_file(
        program_name,
        config_file=program_config_file,
        path=program_file,
    )
    write_workers_scripts(
        worker_config,
        start_path=start_script,
        stop_path=stop_script,
        restart_path=restart_script,
    )
    write_celery_config(
        path=celery_config_file,
        celery_app=app_name,
        log_level=log_level,
        run_dir=run_dir,
        log_dir=log_dir,
    )
    write_beat_script(path=beat_script)

    run_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    install_services(
        environment_file=celery_config_file,
        working_directory=program_file.parent,
        start_script=start_script,
        stop_script=stop_script,
        restart_script=restart_script,
        beat_script=beat_script,
    )
