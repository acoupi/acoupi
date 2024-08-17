import datetime
import shutil
import stat
from pathlib import Path
from typing import Optional

from acoupi.programs.custom.workers import WorkerConfig
from acoupi.system.constants import Settings
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
    settings: Settings,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker start script."""
    path = settings.start_script_path

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_start.sh.jinja2",
            config=config,
            celery_bin=celery_bin,
            app_name=settings.app_name,
            log_level=settings.log_level,
            run_dir=settings.run_dir,
            log_dir=settings.log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_workers_stop_script(
    config: WorkerConfig,
    settings: Settings,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker stop script."""
    path = settings.stop_script_path

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_stop.sh.jinja2",
            config=config,
            celery_bin=celery_bin,
            app_name=settings.app_name,
            log_level=settings.log_level,
            run_dir=settings.run_dir,
            log_dir=settings.log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_workers_restart_script(
    config: WorkerConfig,
    settings: Settings,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker restart script."""
    path = settings.restart_script_path

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_restart.sh.jinja2",
            config=config,
            celery_bin=celery_bin,
            app_name=settings.app_name,
            log_level=settings.log_level,
            run_dir=settings.run_dir,
            log_dir=settings.log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_beat_script(
    settings: Settings,
    celery_bin: Optional[Path] = None,
):
    """Write the beat script."""
    path = settings.beat_script_path

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if celery_bin is None:
        celery_bin = get_celery_bin()

    path.write_text(
        render_template(
            "acoupi_beat.sh.jinja2",
            celery_bin=celery_bin,
            app_name=settings.app_name,
            log_level=settings.log_level,
            run_dir=settings.run_dir,
            log_dir=settings.log_dir,
            now=datetime.datetime.now(),
        )
    )
    give_executable_permissions(path)


def write_scripts(
    config: WorkerConfig,
    settings: Settings,
    celery_bin: Optional[Path] = None,
) -> None:
    """Write the worker scripts."""
    write_workers_start_script(
        config,
        settings,
        celery_bin=celery_bin,
    )
    write_workers_stop_script(
        config,
        settings,
        celery_bin=celery_bin,
    )
    write_workers_restart_script(
        config,
        settings,
        celery_bin=celery_bin,
    )
    write_beat_script(settings, celery_bin=celery_bin)
