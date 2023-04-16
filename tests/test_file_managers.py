"""Test Acoupi file managers."""
import datetime

import pytest

from acoupi import file_managers, types


def test_date_file_manager_save_recording(tmp_path):
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
    recording = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
    )
    # make sure the recording file exists
    path.touch()

    # create a file manager
    file_manager = file_managers.DateFileManager(directory)

    # Act
    file_path = file_manager.save_recording(recording)

    # Assert
    assert directory.exists()
    assert file_path == str(
        directory / "2023" / "4" / "15" / f"180930_{recording.id}.wav"
    )


def test_date_file_manager_fails_if_recording_has_no_path(tmp_path):
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
    recording = types.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
    )

    # create a file manager
    file_manager = file_managers.DateFileManager(directory)

    # Act and Assert
    with pytest.raises(ValueError):
        file_manager.save_recording(recording)


def test_date_file_manager_fails_if_recording_file_does_not_exist(tmp_path):
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
    recording = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
    )

    # make sure the recording file does not exist
    path.unlink(missing_ok=True)

    # create a file manager
    file_manager = file_managers.DateFileManager(directory)

    # Act and Assert
    with pytest.raises(FileNotFoundError):
        file_manager.save_recording(recording)


def test_date_file_manager_delete_recording(tmp_path):
    """Test DateFileManager.delete_recording."""
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
    recording = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime(year, month, day, hour, minute, second),
    )
    # make sure the recording file exists
    path.touch()

    # create a file manager
    file_manager = file_managers.DateFileManager(directory)

    # Act
    file_manager.delete_recording(recording)

    # Assert
    assert not path.exists()

    # Make sure the delete_recording is idempotent
    file_manager.delete_recording(recording)
    assert not path.exists()


def test_date_file_manager_delete_recording_does_not_fail(
    tmp_path,
):
    """Test DateFileManager.delete_recording does not fail.

    If the recording has no path or the file does not exist.
    """
    # Arrange
    directory = tmp_path / "recordings"
    path = tmp_path / "test.wav"

    year = 2023
    month = 4
    day = 15
    hour = 18
    minute = 9
    second = 30
    date = datetime.datetime(year, month, day, hour, minute, second)

    # create a recording without file
    recording_without_file = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=date,
    )
    # Make sure the recording file does not exist
    path.unlink(missing_ok=True)

    # create a recording without path
    recording_without_path = types.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=date,
    )

    # create a file manager
    file_manager = file_managers.DateFileManager(directory)

    # Act
    file_manager.delete_recording(recording_without_file)
    file_manager.delete_recording(recording_without_path)


def test_id_file_manager_save_recording(tmp_path):
    """Test IDFileManager.save_recording."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    recording = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
    )
    # make sure the recording file exists
    path.touch()

    # create a file manager
    file_manager = file_managers.IDFileManager(directory)

    # Act
    file_path = file_manager.save_recording(recording)

    # Assert
    assert directory.exists()
    assert file_path == str(directory / f"{recording.id}.wav")


def test_id_file_manager_fails_if_recording_has_no_path(tmp_path):
    """Test IDFileManager.save_recording fails if recording has no path."""
    # Arrange
    directory = tmp_path / "recordings"

    # create a recording
    recording = types.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
    )

    # create a file manager
    file_manager = file_managers.IDFileManager(directory)

    # Act and Assert
    with pytest.raises(ValueError):
        file_manager.save_recording(recording)


def test_id_file_manager_fails_if_recording_file_does_not_exist(tmp_path):
    """Test IDFileManager.save_recording fails if recording file does not exist."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    recording = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
    )

    # make sure the recording file does not exist
    path.unlink(missing_ok=True)

    # create a file manager
    file_manager = file_managers.IDFileManager(directory)

    # Act and Assert
    with pytest.raises(FileNotFoundError):
        file_manager.save_recording(recording)


def test_id_file_manager_delete_recording(tmp_path):
    """Test IDFileManager.delete_recording."""
    # Arrange
    path = tmp_path / "test.wav"
    directory = tmp_path / "recordings"

    # create a recording
    recording = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
    )
    # make sure the recording file exists
    path.touch()

    # create a file manager
    file_manager = file_managers.IDFileManager(directory)

    # Act
    file_manager.delete_recording(recording)

    # Assert
    assert not path.exists()

    # Make sure the delete_recording is idempotent
    file_manager.delete_recording(recording)
    assert not path.exists()


def test_id_file_manager_delete_recording_does_not_fail(tmp_path):
    """Test IDFileManager.delete_recording does not fail.

    If the recording has no path or the file does not exist.
    """
    # Arrange
    directory = tmp_path / "recordings"
    path = tmp_path / "test.wav"

    # create a recording without file
    recording_without_file = types.Recording(
        path=str(path),
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
    )
    # Make sure the recording file does not exist
    path.unlink(missing_ok=True)

    # create a recording without path
    recording_without_path = types.Recording(
        path=None,
        duration=1,
        samplerate=8000,
        datetime=datetime.datetime.now(),
    )

    # create a file manager
    file_manager = file_managers.IDFileManager(directory)

    # Act
    file_manager.delete_recording(recording_without_file)
    file_manager.delete_recording(recording_without_path)
