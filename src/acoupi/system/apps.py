"""System functions for managing celery apps."""

from celery import Celery

from acoupi.system.constants import Settings
from acoupi.system.programs import load_program

__all__ = [
    "get_celery_app",
]


def get_celery_app(
    settings: Settings,
) -> Celery:
    """Get the currently setup celery app."""
    program = load_program(settings)
    return program.app
