"""System functions to manage acoupi services."""
import subprocess
from pathlib import Path
from typing import Optional

from acoupi.system.constants import (
    ACOUPI_BEAT_SERVICE_FILE,
    ACOUPI_HOME,
    ACOUPI_SERVICE_FILE,
    BEAT_SCRIPT_PATH,
    CELERY_CONFIG_PATH,
    RESTART_SCRIPT_PATH,
    START_SCRIPT_PATH,
    STOP_SCRIPT_PATH,
)
from acoupi.system.templates import render_template

__all__ = [
    "install_services",
    "uninstall_services",
    "services_are_installed"
    "start_services",
    "stop_services",
    "enable_services",
    "disable_services",
]


def get_user_unit_dir() -> Path:
    """Get the user unit directory.

    Use `pkg-config` to find the user unit directory.

    Returns
    -------
    Path
        The user unit directory.

    Raises
    ------
    subprocess.CalledProcessError
        If `pkg-config` returns a non-zero exit code.
    """
    # NOTE: Might need to revisit this in case systemd
    # user unit directory changes in other platforms.
    return Path.home() / ".config" / "systemd" / "user"


def install_services(
    path: Optional[Path] = None,
    environment_file: Path = CELERY_CONFIG_PATH,
    working_directory: Path = ACOUPI_HOME,
    start_script: Path = START_SCRIPT_PATH,
    stop_script: Path = STOP_SCRIPT_PATH,
    restart_script: Path = RESTART_SCRIPT_PATH,
    beat_script: Path = BEAT_SCRIPT_PATH,
):
    """Install acoupi services."""
    if path is None:
        path = get_user_unit_dir()

    if not path.exists():
        path.mkdir(parents=True)

    acoupi_service_file = path / ACOUPI_SERVICE_FILE
    acoupi_beat_service_file = path / ACOUPI_BEAT_SERVICE_FILE
    acoupi_service_file.write_text(
        render_template(
            "acoupi.service.jinja2",
            environment_file=environment_file,
            working_directory=working_directory,
            start_script=start_script,
            stop_script=stop_script,
            restart_script=restart_script,
        )
    )
    acoupi_beat_service_file.write_text(
        render_template(
            "acoupi_beat.service.jinja2",
            environment_file=environment_file,
            working_directory=working_directory,
            beat_script=beat_script,
        )
    )


def uninstall_services(path: Optional[Path] = None):
    """Uninstall acoupi services."""
    if path is None:
        path = get_user_unit_dir()

    acoupi_service_file = path / ACOUPI_SERVICE_FILE
    acoupi_beat_service_file = path / ACOUPI_BEAT_SERVICE_FILE

    try:
        acoupi_service_file.unlink()
    except FileNotFoundError:
        pass

    try:
        acoupi_beat_service_file.unlink()
    except FileNotFoundError:
        pass


def services_are_installed(path: Optional[Path] = None) -> bool:
    """Check if acoupi services are installed."""
    if path is None:
        path = get_user_unit_dir()

    acoupi_service_file = path / ACOUPI_SERVICE_FILE
    acoupi_beat_service_file = path / ACOUPI_BEAT_SERVICE_FILE
    return acoupi_service_file.exists() and acoupi_beat_service_file.exists()


def enable_services(path: Optional[Path] = None, **kwargs):
    """Enable acoupi services."""
    if not services_are_installed(path):
        install_services(path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "enable", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "enable", "acoupi-beat.service"], check=True
    )


def disable_services(path: Optional[Path] = None, **kwargs):
    """Disable acoupi services."""
    if not services_are_installed(path):
        install_services(path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "disable", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "disable", "acoupi-beat.service"], check=True
    )


def start_services(path: Optional[Path] = None, **kwargs):
    """Start acoupi services."""
    if not services_are_installed(path):
        install_services(path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "start", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "start", "acoupi-beat.service"], check=True
    )


def stop_services(path: Optional[Path] = None, **kwargs):
    """Stop acoupi services."""
    if not services_are_installed(path):
        install_services(path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "stop", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "stop", "acoupi-beat.service"], check=True
    )
