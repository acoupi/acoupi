import shutil
from pathlib import Path

from acoupi.system.constants import (
    APP_NAME,
    BEAT_SCRIPT_PATH,
    CELERY_CONFIG_PATH,
    LOG_DIR,
    LOG_LEVEL,
    RUN_DIR,
)
from acoupi.system.templates import render_template
from acoupi.system.workers import give_executable_permissions

__all__ = [
    "write_celery_config",
    "write_beat_script",
]


def write_celery_config(
    path: Path = CELERY_CONFIG_PATH,
    celery_app: str = APP_NAME,
    log_level: str = LOG_LEVEL,
    run_dir: Path = RUN_DIR,
    log_dir: Path = LOG_DIR,
):
    """Write the celery config file."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    celery_bin = shutil.which("celery")

    path.write_text(
        render_template(
            "celery.jinja2",
            celery_bin=celery_bin,
            celery_app=celery_app,
            log_level=log_level,
            run_dir=run_dir,
            log_dir=log_dir,
        )
    )


def write_beat_script(path: Path = BEAT_SCRIPT_PATH):
    """Write the beat script."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(
        render_template(
            "acoupi_beat.sh.jinja2",
        )
    )
    give_executable_permissions(path)
