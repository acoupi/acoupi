"""Test Acoupi file managers."""
import datetime
from pathlib import Path

import pytest

from acoupi import components, data


def test_date_file_manager_save_recording(
    tmp_path: Path,
    deployment: data.Deployment,
):
    """Test DateFileManager.save_recording."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    year = 2023
    month = 4
    day = 15
    hour = 18
    minute = 9
    second = 30
    recording = data.Recording(
        path=path,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
        deployment=deployment,
    )
    # make sure the recording file exists
    path.touch()

    # create a file manager
    file_manager = components.DateFileManager(directory)

    # Act
    file_path = file_manager.save_recording(recording)

    # Assert
    assert directory.exists()
    assert file_path == (
        directory / "2023" / "4" / "15" / f"180930_{recording.id}.wav"
    )


def test_date_file_manager_fails_if_recording_has_no_path(
    tmp_path: Path, deployment: data.Deployment
):
    """Test DateFileManager.save_recording fails if recording has no path."""
    # Arrange
    directory = tmp_path / "recordings"

    # create a recording
    year = 2023
    month = 4
    day = 15
    hour = 18
    minute = 9
    second = 30
    recording = data.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
        deployment=deployment,
    )

    # create a file manager
    file_manager = components.DateFileManager(directory)

    # Act and Assert
    with pytest.raises(ValueError):
        file_manager.save_recording(recording)


def test_date_file_manager_fails_if_recording_file_does_not_exist(
    tmp_path: Path, deployment: data.Deployment
):
    """Test DateFileManager.save_recording fails if recording file does not exist."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    year = 2023
    month = 4
    day = 15
    hour = 18
    minute = 9
    second = 30
    recording = data.Recording(
        path=path,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
        deployment=deployment,
    )

    # make sure the recording file does not exist
    path.unlink(missing_ok=True)

    # create a file manager
    file_manager = components.DateFileManager(directory)

    # Act and Assert
    with pytest.raises(FileNotFoundError):
        file_manager.save_recording(recording)


def test_id_file_manager_save_recording(
    tmp_path: Path, deployment: data.Deployment
):
    """Test IDFileManager.save_recording."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    recording = data.Recording(
        path=path,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
        deployment=deployment,
    )
    # make sure the recording file exists
    path.touch()

    # create a file manager
    file_manager = components.IDFileManager(directory)

    # Act
    file_path = file_manager.save_recording(recording)

    # Assert
    assert directory.exists()
    assert file_path == directory / f"{recording.id}.wav"


def test_id_file_manager_fails_if_recording_has_no_path(
    tmp_path: Path, deployment: data.Deployment
):
    """Test IDFileManager.save_recording fails if recording has no path."""
    # Arrange
    directory = tmp_path / "recordings"

    # create a recording
    recording = data.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
        deployment=deployment,
    )

    # create a file manager
    file_manager = components.IDFileManager(directory)

    # Act and Assert
    with pytest.raises(ValueError):
        file_manager.save_recording(recording)


def test_id_file_manager_fails_if_recording_file_does_not_exist(
    tmp_path: Path, deployment: data.Deployment
):
    """Test IDFileManager.save_recording fails if recording file does not exist."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    recording = data.Recording(
        path=path,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
        deployment=deployment,
    )

    # make sure the recording file does not exist
    path.unlink(missing_ok=True)

    # create a file manager
    file_manager = components.IDFileManager(directory)

    # Act and Assert
    with pytest.raises(FileNotFoundError):
        file_manager.save_recording(recording)
