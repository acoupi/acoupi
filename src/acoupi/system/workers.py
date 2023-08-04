import stat
from pathlib import Path

from acoupi.programs.workers import WorkerConfig
from acoupi.system.constants import (
    RESTART_SCRIPT_PATH,
    START_SCRIPT_PATH,
    STOP_SCRIPT_PATH,
)
from acoupi.system.templates import render_template

__all__ = [
    "write_workers_scripts",
]


def give_executable_permissions(path: Path) -> None:
    """Give executable permissions to a file."""
    path.chmod(
        path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def write_workers_start_script(
    config: WorkerConfig,
    path: Path = START_SCRIPT_PATH,
) -> None:
    """Write the worker start script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "acoupi_start.sh.jinja2",
            config=config,
        )
    )
    give_executable_permissions(path)


def write_workers_stop_script(
    config: WorkerConfig,
    path: Path = STOP_SCRIPT_PATH,
) -> None:
    """Write the worker stop script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "workers_stop.sh.jinja2",
            config=config,
        )
    )
    give_executable_permissions(path)


def write_workers_restart_script(
    config: WorkerConfig,
    path: Path = RESTART_SCRIPT_PATH,
) -> None:
    """Write the worker restart script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "acoupi_restart.sh.jinja2",
            config=config,
        )
    )
    give_executable_permissions(path)


def write_workers_scripts(
    config: WorkerConfig,
    start_path: Path = START_SCRIPT_PATH,
    stop_path: Path = STOP_SCRIPT_PATH,
    restart_path: Path = RESTART_SCRIPT_PATH,
) -> None:
    """Write the worker scripts."""
    write_workers_start_script(config, start_path)
    write_workers_stop_script(config, stop_path)
    write_workers_restart_script(config, restart_path)
