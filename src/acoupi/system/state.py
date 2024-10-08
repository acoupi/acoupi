"""Functions for accessing the state of the Acoupi system."""

from pydantic import BaseModel

from acoupi.system.celery import CeleryStatus, get_celery_status
from acoupi.system.constants import Settings
from acoupi.system.programs import ProgramState, get_program_state
from acoupi.system.services import (
    ServiceStatus,
    get_acoupi_beat_service_status,
    get_acoupi_service_status,
)

__all__ = [
    "is_configured",
    "get_status",
    "AcoupiStatus",
]


class ServicesStatus(BaseModel):
    acoupi: ServiceStatus
    beat: ServiceStatus


class AcoupiStatus(BaseModel):
    """Model representing the status of the Acoupi system.

    Attributes
    ----------
    acoupi_service : ServiceStatus
        The status of the acoupi systemd service.
    beat_service : ServiceStatus
        The status of the beat systemd service.
    celery : CeleryStatus
        The status of the Celery workers.
    program : ProgramStatus
        The status of the acoupi program.
    """

    services: ServicesStatus
    celery: CeleryStatus
    program: ProgramState


def is_configured(settings: Settings) -> bool:
    """Check if acoupi is configured.

    Parameters
    ----------
    settings
        The current acoupi settings

    Returns
    -------
    bool
        True if all required configuration files are correctly set up.
    """
    return (
        settings.program_config_file.exists()
        and settings.program_file.exists()
        and settings.program_name_file.exists()
    )


def get_status(settings: Settings) -> AcoupiStatus:
    """Get the current status of the Acoupi system.

    Parameters
    ----------
    settings : Settings
        The settings object containing configuration paths.

    Returns
    -------
    AcoupiStatus
        An object containing the status of various components of the Acoupi
        system.
    """
    acoupi_service_status = get_acoupi_service_status(settings)
    beat_service_status = get_acoupi_beat_service_status(settings)
    celery_status = get_celery_status(settings)
    program_state = get_program_state(settings)
    return AcoupiStatus(
        services=ServicesStatus(
            acoupi=acoupi_service_status,
            beat=beat_service_status,
        ),
        celery=celery_status,
        program=program_state,
    )
