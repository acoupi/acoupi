"""Test suite for system deployment functions."""

import pytest

from acoupi import data
from acoupi.system import Settings, deployments, exceptions


def test_start_deployment_saves_deployment_in_file(settings: Settings):
    """Test that create_deployment saves the deployment in the file."""
    deployment = deployments.start_deployment(settings, name="test")

    assert isinstance(deployment, data.Deployment)
    assert settings.deployment_file.exists()
    contents = settings.deployment_file.read_text()
    recovered = data.Deployment.model_validate_json(contents)
    assert recovered == deployment
    assert recovered.name == "test"
    assert recovered.started_on is not None
    assert recovered.ended_on is None


def test_start_deployment_with_location_info(settings: Settings):
    """Test that create_deployment saves the deployment in the file."""
    deployment = deployments.start_deployment(
        settings,
        name="test",
        latitude=1,
        longitude=2,
    )

    assert isinstance(deployment, data.Deployment)
    assert deployment.latitude == 1
    assert deployment.longitude == 2
    assert settings.deployment_file.exists()
    contents = settings.deployment_file.read_text()
    recovered = data.Deployment.model_validate_json(contents)
    assert recovered == deployment


def test_start_deployment_fails_if_already_deployed(settings: Settings):
    """Test that create_deployment fails if already deployed."""
    deployments.start_deployment(settings, name="test")
    with pytest.raises(exceptions.DeploymentError):
        deployments.start_deployment(settings, name="test2")


def test_end_deployment_saves_end_time(settings: Settings):
    """Test that end_deployment saves the end time."""
    deployments.start_deployment(settings, name="test")
    deployments.end_deployment(settings)

    assert settings.deployment_file.exists()
    contents = settings.deployment_file.read_text()
    deployment = data.Deployment.model_validate_json(contents)
    assert deployment.ended_on is not None


def test_start_deployment_after_ending_previous(settings: Settings):
    """Test that create_deployment works after ending the previous."""
    deployments.start_deployment(settings, name="test")
    deployments.end_deployment(settings)
    deployments.start_deployment(settings, name="test2")

    assert settings.deployment_file.exists()
    contents = settings.deployment_file.read_text()
    deployment = data.Deployment.model_validate_json(contents)
    assert deployment.name == "test2"
    assert deployment.started_on is not None
    assert deployment.ended_on is None


def test_end_deployment_fails_if_not_deployed(settings: Settings):
    """Test that end_deployment fails if not deployed."""
    with pytest.raises(exceptions.DeploymentError):
        deployments.end_deployment(settings)


def test_get_deployment_fails_if_hasnt_been_deployed(settings: Settings):
    """Test that get_deployment fails if the deployment hasn't been deployed."""
    with pytest.raises(exceptions.DeploymentError):
        deployments.get_current_deployment(settings)


def test_get_current_deployment(settings: Settings):
    """Test that get_deployment returns the current deployment."""
    deployments.start_deployment(
        settings, name="test", latitude=1, longitude=2
    )
    deployment = deployments.get_current_deployment(settings)
    assert isinstance(deployment, data.Deployment)
    assert deployment.name == "test"
    assert deployment.latitude == 1
    assert deployment.longitude == 2
    assert deployment.started_on is not None
    assert deployment.ended_on is None


def test_get_current_deployment_fails_if_ended(settings: Settings):
    """Test that get_deployment fails if the deployment has ended."""
    deployments.start_deployment(settings, name="test")
    deployments.end_deployment(settings)
    with pytest.raises(exceptions.DeploymentError):
        deployments.get_current_deployment(settings)
