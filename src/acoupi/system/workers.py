from pathlib import Path

from acoupi.programs.workers import WorkerConfig
from acoupi.system.constants import ACOUPI_HOME
from acoupi.system.templates import render_template

__all__ = [
    "write_workers_scripts",
]

WORKER_START_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-worker-start.sh"
WORKER_STOP_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-worker-stop.sh"
WORKER_RESTART_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-worker-restart.sh"


def write_workers_start_script(
    config: WorkerConfig,
    path: Path = WORKER_START_SCRIPT_PATH,
) -> None:
    """Write the worker start script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "workers_start.sh.jinja2",
            config=config,
        )
    )


def write_workers_stop_script(
    config: WorkerConfig,
    path: Path = WORKER_STOP_SCRIPT_PATH,
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


def write_workers_restart_script(
    config: WorkerConfig,
    path: Path = WORKER_RESTART_SCRIPT_PATH,
) -> None:
    """Write the worker restart script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "workers_restart.sh.jinja2",
            config=config,
        )
    )


def write_workers_scripts(
    config: WorkerConfig,
    start_path: Path = WORKER_START_SCRIPT_PATH,
    stop_path: Path = WORKER_STOP_SCRIPT_PATH,
    restart_path: Path = WORKER_RESTART_SCRIPT_PATH,
) -> None:
    """Write the worker scripts."""
    write_workers_start_script(config, start_path)
    write_workers_stop_script(config, stop_path)
    write_workers_restart_script(config, restart_path)
