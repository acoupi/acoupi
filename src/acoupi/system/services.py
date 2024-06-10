"""System functions to manage acoupi services."""

import subprocess
from pathlib import Path
from typing import Optional

from acoupi.system.constants import Settings
from acoupi.system.templates import render_template

__all__ = [
    "install_services",
    "uninstall_services",
    "services_are_installed",
    "start_services",
    "stop_services",
    "enable_services",
    "disable_services",
    "status_services",
]


def get_user_unit_dir() -> Path:
    """Get the user unit directory.

    Returns
    -------
    Path
        The user unit directory.
    """
    # NOTE: Might need to revisit this in case systemd
    # user unit directory changes in other platforms.
    return Path.home() / ".config" / "systemd" / "user"


def install_services(
    settings: Settings,
    path: Optional[Path] = None,
):
    """Install acoupi services."""
    if path is None:
        path = get_user_unit_dir()

    if not path.exists():
        path.mkdir(parents=True)

    acoupi_service_file = path / settings.acoupi_service_file
    acoupi_beat_service_file = path / settings.acoupi_beat_service_file
    acoupi_service_file.write_text(
        render_template(
            "acoupi.service.jinja2",
            environment_file=settings.celery_config_file,
            working_directory=settings.home,
            start_script=settings.start_script_path,
            stop_script=settings.stop_script_path,
            restart_script=settings.restart_script_path,
        )
    )
    acoupi_beat_service_file.write_text(
        render_template(
            "acoupi_beat.service.jinja2",
            environment_file=settings.celery_config_file,
            working_directory=settings.home,
            beat_script=settings.beat_script_path,
        )
    )


def uninstall_services(settings: Settings, path: Optional[Path] = None):
    """Uninstall acoupi services."""
    if path is None:
        path = get_user_unit_dir()

    acoupi_service_file = path / settings.acoupi_service_file
    acoupi_beat_service_file = path / settings.acoupi_beat_service_file

    try:
        acoupi_service_file.unlink()
    except FileNotFoundError:
        pass

    try:
        acoupi_beat_service_file.unlink()
    except FileNotFoundError:
        pass


def services_are_installed(
    settings: Settings, path: Optional[Path] = None
) -> bool:
    """Check if acoupi services are installed."""
    if path is None:
        path = get_user_unit_dir()

    acoupi_service_file = path / settings.acoupi_service_file
    acoupi_beat_service_file = path / settings.acoupi_beat_service_file
    return acoupi_service_file.exists() and acoupi_beat_service_file.exists()


def enable_services(settings: Settings, path: Optional[Path] = None, **kwargs):
    """Enable acoupi services."""
    if not services_are_installed(settings, path):
        install_services(settings, path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "enable", "acoupi.service"],
        check=True,
    )
    subprocess.run(
        ["systemctl", "--user", "enable", "acoupi-beat.service"],
        check=True,
    )


def disable_services(
    settings: Settings, path: Optional[Path] = None, **kwargs
):
    """Disable acoupi services."""
    if not services_are_installed(settings, path):
        install_services(settings, path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "disable", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "disable", "acoupi-beat.service"], check=True
    )


def start_services(settings: Settings, path: Optional[Path] = None, **kwargs):
    """Start acoupi services."""
    if not services_are_installed(settings, path):
        install_services(settings, path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "start", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "start", "acoupi-beat.service"], check=True
    )


def stop_services(settings: Settings, path: Optional[Path] = None, **kwargs):
    """Stop acoupi services."""
    if not services_are_installed(settings, path):
        install_services(settings, path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "stop", "acoupi.service"], check=True
    )
    subprocess.run(
        ["systemctl", "--user", "stop", "acoupi-beat.service"], check=True
    )


def status_services(settings: Settings, path: Optional[Path] = None, **kwargs):
    """Stop acoupi services."""
    if not services_are_installed(settings, path):
        install_services(settings, path, **kwargs)

    subprocess.run(
        ["systemctl", "--user", "status", "acoupi.service"], text=True
    )
    subprocess.run(
        ["systemctl", "--user", "status", "acoupi-beat.service"], text=True
    )
