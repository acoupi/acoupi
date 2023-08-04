import shutil
from pathlib import Path

from acoupi.system.constants import (
    APP_NAME,
    CELERY_CONFIG_PATH,
    LOG_DIR,
    LOG_LEVEL,
    RUN_DIR,
)
from acoupi.system.templates import render_template


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
