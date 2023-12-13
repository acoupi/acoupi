import datetime
import shutil
import stat
from pathlib import Path
from typing import Optional

from acoupi.programs.workers import WorkerConfig
from acoupi.system.constants import (
    APP_NAME,
    BEAT_SCRIPT_PATH,
    LOG_DIR,
    LOG_LEVEL,
    RESTART_SCRIPT_PATH,
    RUN_DIR,
    START_SCRIPT_PATH,
    STOP_SCRIPT_PATH,
)
from acoupi.system.templates import render_template

__all__ = [
    "write_scripts",
]


def get_celery_bin() -> Path:
    """Return the path to the celery binary."""
    path = shutil.which("celery")
    if path is None:
        raise RuntimeError("Could not find celery binary.")
    return Path(path)


def give_executable_permissions(path: Path) -> None:
    """Give executable permissions to a file."""
    path.chmod(
        path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def write_workers_start_script(
    config: WorkerConfig,
    path: Path = START_SCRIPT_PATH,
    app_name: str = APP_NAME,
    log_level: str = LOG_LEVEL,
    run_dir: Path = RUN_DIR,
    log_dir: Path = LOG_DIR,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker start script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_start.sh.jinja2",
            config=config,
            celery_bin=celery_bin,
            app_name=app_name,
            log_level=log_level,
            run_dir=run_dir,
            log_dir=log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_workers_stop_script(
    config: WorkerConfig,
    path: Path = STOP_SCRIPT_PATH,
    app_name: str = APP_NAME,
    log_level: str = LOG_LEVEL,
    run_dir: Path = RUN_DIR,
    log_dir: Path = LOG_DIR,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker stop script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_stop.sh.jinja2",
            config=config,
            celery_bin=celery_bin,
            app_name=app_name,
            log_level=log_level,
            run_dir=run_dir,
            log_dir=log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_workers_restart_script(
    config: WorkerConfig,
    path: Path = RESTART_SCRIPT_PATH,
    app_name: str = APP_NAME,
    log_level: str = LOG_LEVEL,
    run_dir: Path = RUN_DIR,
    log_dir: Path = LOG_DIR,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker restart script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_restart.sh.jinja2",
            config=config,
            celery_bin=celery_bin,
            app_name=app_name,
            log_level=log_level,
            run_dir=run_dir,
            log_dir=log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_beat_script(
    path: Path = BEAT_SCRIPT_PATH,
    app_name: str = APP_NAME,
    log_level: str = LOG_LEVEL,
    run_dir: Path = RUN_DIR,
    log_dir: Path = LOG_DIR,
    celery_bin: Optional[Path] = None,
):
    """Write the beat script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_beat.sh.jinja2",
            celery_bin=celery_bin,
            app_name=app_name,
            log_level=log_level,
            run_dir=run_dir,
            log_dir=log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_scripts(
    config: WorkerConfig,
    start_path: Path = START_SCRIPT_PATH,
    stop_path: Path = STOP_SCRIPT_PATH,
    restart_path: Path = RESTART_SCRIPT_PATH,
    beat_path: Path = BEAT_SCRIPT_PATH,
    app_name: str = APP_NAME,
    log_level: str = LOG_LEVEL,
    run_dir: Path = RUN_DIR,
    log_dir: Path = LOG_DIR,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker scripts."""
    write_workers_start_script(
        config,
        path=start_path,
        app_name=app_name,
        log_level=log_level,
        run_dir=run_dir,
        log_dir=log_dir,
        celery_bin=celery_bin,
    )
    write_workers_stop_script(
        config,
        path=stop_path,
        app_name=app_name,
        log_level=log_level,
        run_dir=run_dir,
        log_dir=log_dir,
        celery_bin=celery_bin,
    )
    write_workers_restart_script(
        config,
        path=restart_path,
        app_name=app_name,
        log_level=log_level,
        run_dir=run_dir,
        log_dir=log_dir,
        celery_bin=celery_bin,
    )
    write_beat_script(
        path=beat_path,
        app_name=app_name,
        log_level=log_level,
        run_dir=run_dir,
        log_dir=log_dir,
        celery_bin=celery_bin,
    )
