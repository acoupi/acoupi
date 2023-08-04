"""System functions for managing Acoupi programs."""
import inspect
from importlib import import_module
from pathlib import Path
from typing import Type

from acoupi import programs
from acoupi.system.templates import render_template
from acoupi.system.constants import CONFIG_PATH, PROGRAM_PATH

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
    config_file: Path = CONFIG_PATH,
    program_file: Path = PROGRAM_PATH,
) -> None:
    """Write the python script with the celery app to run."""
    if not program_file.parent.exists():
        program_file.parent.mkdir(parents=True)

    with open(program_file, "w") as file:
        file.write(
            render_template(
                "app.py.jinja2",
                program_name=program_name,
                config_file=config_file,
            )
        )
