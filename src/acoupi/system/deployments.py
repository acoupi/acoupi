"""Functions that manage Acoupi system.

This module contains utility functions for acoupi programs
such as loading programs and getting celery apps from programs.
"""
import datetime
from pathlib import Path
from typing import Optional

from acoupi import data
from acoupi.system.constants import Settings
from acoupi.system.exceptions import DeploymentError

__all__ = [
    "get_current_deployment",
    "start_deployment",
    "end_deployment",
]


def start_deployment(
    settings: Settings,
    name: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> data.Deployment:
    """Start a new deployment.

    Parameters
    ----------
    settings : Settings
        The settings to use.
    name : str
        The name of the deployment.

    Returns
    -------
    data.Deployment

    Raises
    ------
    DeploymentError
        If Acoupi has already been deployed.
    ValueError
        If the deployment data is invalid. i.e. the latitude or longitude
        is invalid.
    """
    deployment = None
    try:
        deployment = get_current_deployment(settings)
    except DeploymentError:
        pass

    if deployment is not None:
        raise DeploymentError("Acoupi has already been deployed.")

    deployment = data.Deployment(
        name=name,
        started_on=datetime.datetime.now(),
        latitude=latitude,
        longitude=longitude,
    )
    write_deployment_to_file(deployment, settings.deployment_file)
    return deployment


def get_current_deployment(settings: Settings) -> data.Deployment:
    """Get current deployment.

    Parameters
    ----------
    settings : Settings
        The settings to use.

    Returns
    -------
    data.Deployment
        The current deployment.

    Raises
    ------
    DeploymentError
        If the deployment file does not exist or the deployment has already
        ended.

    """
    try:
        deployment = load_deployment_from_file(settings.deployment_file)
    except FileNotFoundError as error:
        raise DeploymentError("Acoupi has not been deployed yet.") from error

    if deployment.ended_on is not None:
        raise DeploymentError("Acoupi deployment has already ended.")

    return deployment


def end_deployment(settings: Settings) -> data.Deployment:
    """End current deployment.

    Parameters
    ----------
    settings : Settings
        The settings to use.

    Returns
    -------
    data.Deployment
        The ended deployment.

    Raises
    ------
    DeploymentError
        If the deployment has already ended or has not been started yet.
    """
    deployment = get_current_deployment(settings)
    deployment.ended_on = datetime.datetime.now()
    write_deployment_to_file(deployment, settings.deployment_file)
    return deployment


def write_deployment_to_file(deployment: data.Deployment, path: Path) -> None:
    """Write deployment to file.

    The deployment is written as a JSON file.

    Parameters
    ----------
    deployment : data.Deployment
        The deployment to write to file.
    path : Path
        The path to write the deployment to.
    """
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    path.write_text(deployment.model_dump_json(exclude_none=True))


def load_deployment_from_file(path: Path) -> data.Deployment:
    """Load deployment from file.

    The deployment is loaded from a JSON file.

    Parameters
    ----------
    path : Path
        The path to load the deployment from.

    Returns
    -------
    data.Deployment
        The loaded deployment.

    Raises
    ------
    ValueError
        If the deployment data is invalid.
    FileNotFoundError
        If the deployment file does not exist.
    """
    return data.Deployment.model_validate_json(path.read_text())
