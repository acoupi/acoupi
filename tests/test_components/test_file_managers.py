"""Test Acoupi file managers."""

import datetime
from pathlib import Path

import pytest

from acoupi import components, data


def test_save_recording_manager_fails_if_recording_has_no_path(
    deployment: data.Deployment,
    tmp_path: Path,
):
    manager = components.SaveRecordingManager(tmp_path)
    recording = data.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
        deployment=deployment,
    )

    with pytest.raises(ValueError):
        manager.update_recording_path(recording)


def test_save_recording_with_confident_tags(tmp_path: Path):
    audio_dir = tmp_path / "audio"
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    recording_file = tmp_dir / "recording.wav"
    recording_file.touch()
    recording_file.write_text("test content")
    recording = data.Recording(
        path=recording_file,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
        deployment=data.Deployment(name="test"),
    )
    model_output = data.ModelOutput(
        name_model="test_model",
        recording=recording,
        tags=[
            data.PredictedTag(
                tag=data.Tag(key="test", value="value1"),
                classification_probability=0.6,
            ),
            data.PredictedTag(
                tag=data.Tag(key="test", value="value2"),
                classification_probability=0.3,
            ),
        ],
    )
    manager = components.SaveRecordingManager(
        audio_dir, detection_threshold=0.6, saving_threshold=0.5
    )

    new_path = manager.update_recording_path(
        recording, model_outputs=[model_output]
    )
    assert not recording_file.exists()
    assert new_path.parent == audio_dir / "true_detections"
    assert new_path.exists()
    assert new_path.read_text() == "test content"


def test_save_recording_with_unconfident_tags(tmp_path: Path):
    audio_dir = tmp_path / "audio"
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    recording_file = tmp_dir / "recording.wav"
    recording_file.touch()
    recording_file.write_text("test content")
    recording = data.Recording(
        path=recording_file,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
        deployment=data.Deployment(name="test"),
    )
    model_output = data.ModelOutput(
        name_model="test_model",
        recording=recording,
        tags=[
            data.PredictedTag(
                tag=data.Tag(key="test", value="value1"),
                classification_probability=0.4,
            ),
            data.PredictedTag(
                tag=data.Tag(key="test", value="value2"),
                classification_probability=0.3,
            ),
        ],
    )
    manager = components.SaveRecordingManager(
        audio_dir,
        detection_threshold=0.6,
        saving_threshold=0.4,
    )

    new_path = manager.update_recording_path(
        recording, model_outputs=[model_output]
    )
    assert not recording_file.exists()
    assert new_path.parent == audio_dir / "false_detections"
    assert new_path.exists()
    assert new_path.read_text() == "test content"


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
    file_path = file_manager.update_recording_path(recording)

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
        file_manager.update_recording_path(recording)


def test_date_file_manager_fails_if_recording_file_does_not_exist(
    tmp_path: Path, deployment: data.Deployment
):
    """Test DateFileManager.save_recording fails if recording file does not
    exist.
    """
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
    try:
        path.unlink()
    except FileNotFoundError:
        pass

    # create a file manager
    file_manager = components.DateFileManager(directory)

    # Act and Assert
    with pytest.raises(FileNotFoundError):
        file_manager.update_recording_path(recording)


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
    file_path = file_manager.update_recording_path(recording)

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
        file_manager.update_recording_path(recording)


def test_id_file_manager_fails_if_recording_file_does_not_exist(
    tmp_path: Path, deployment: data.Deployment
):
    """Test IDFileManager.save_recording fails if recording file does not
    exist.
    """
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
    try:
        path.unlink()
    except FileNotFoundError:
        pass

    # create a file manager
    file_manager = components.IDFileManager(directory)

    # Act and Assert
    with pytest.raises(FileNotFoundError):
        file_manager.update_recording_path(recording)
