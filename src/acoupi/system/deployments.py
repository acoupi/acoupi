"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""
import datetime

from acoupi import data

__all__ = ["get_current_deployment"]


def get_current_deployment() -> data.Deployment:
    """Get current deployment."""
    # TODO: implement this better
    return data.Deployment(
        name="default",
        started_on=datetime.datetime.now(),
    )
