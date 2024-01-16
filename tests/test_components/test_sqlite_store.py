"""Test the SQLite store."""
import datetime
import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from acoupi import components, data


@pytest.fixture(scope="function")
def sqlite_store(
    tmp_path: Path,
) -> Generator[components.SqliteStore, None, None]:
    """Create a store."""
    db_path = tmp_path / "test.db"
    yield components.SqliteStore(db_path)
    db_path.unlink()


def test_sqlite_store_creates_a_database_file(
    sqlite_store: components.SqliteStore,
) -> None:
    """Test that the store creates a database file."""
    db_path = sqlite_store.db_path
    assert db_path.exists()


def test_database_has_correct_tables(
    sqlite_store: components.SqliteStore,
) -> None:
    """Test that the database has the correct tables."""
    expected_tables = {
        "recording",
        "deployment",
        "detection",
    }
    db_path = sqlite_store.db_path

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        actual_tables = set(row[0] for row in cursor.fetchall())
        assert expected_tables.issubset(actual_tables)


def test_recording_table_has_correct_columns(
    sqlite_store: components.SqliteStore,
) -> None:
    """Test that the recording table has the correct columns."""
    expected_columns = {
        "id",
        "path",
        "duration_s",
        "samplerate_hz",
        "audio_channels",
        "datetime",
        "deployment_id",
    }
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_table_has_correct_columns(sqlite_store) -> None:
    """Test that the deployment table has the correct columns."""
    expected_columns = {
        "id",
        "started_on",
        "latitude",
        "longitude",
        "name",
    }
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(deployment);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_can_instantiate_multiple_stores_with_the_same_sqlite_file(
    tmp_path: Path,
) -> None:
    """Test that we can instantiate multiple stores to the same sqlite file."""
    # Arrange
    db_path = tmp_path / "test.db"

    # Act
    store1 = components.SqliteStore(db_path)
    store2 = components.SqliteStore(db_path)

    # Assert
    assert store1 is not None
    assert store2 is not None


def test_can_store_a_deployment(sqlite_store: components.SqliteStore) -> None:
    """Test that we can store a deployment."""
    # Arrange
    now = datetime.datetime.now()
    deployment = data.Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        name="test_device",
    )

    # Act
    sqlite_store.store_deployment(deployment)

    # Assert
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deployment;")
        row = cursor.fetchone()
        assert row["started_on"] == now.isoformat(sep=" ")
        assert row["latitude"] == 1.0
        assert row["longitude"] == 2.0


def test_get_current_deployment_returns_new_if_no_deployment_exists(
    sqlite_store: components.SqliteStore,
    patched_now,
) -> None:
    """Test that get_current_deployment fails if no deployment exists."""
    # Arrange
    # Patch the current time
    now = patched_now()

    # Make sure there are no deployments
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deployment;")

    # Act
    # Try to get the current deployment, this should create a new one
    deployment = sqlite_store.get_current_deployment()

    # Assert
    assert deployment.latitude is None
    assert deployment.longitude is None
    assert deployment.started_on == now


def test_get_current_deployment_gets_latest_deployment(
    sqlite_store: components.SqliteStore,
) -> None:
    """Test that get_current_deployment gets the latest deployment."""
    # Arrange
    start_1 = datetime.datetime.now()
    start_2 = datetime.datetime.now() - datetime.timedelta(days=10)
    deployment1 = data.Deployment(
        started_on=start_1,
        latitude=1.0,
        longitude=2.0,
        name="test_device",
    )
    deployment2 = data.Deployment(
        started_on=start_2,
        latitude=3.0,
        longitude=4.0,
        name="test_device",
    )
    sqlite_store.store_deployment(deployment1)
    sqlite_store.store_deployment(deployment2)

    # Act
    deployment = sqlite_store.get_current_deployment()

    # Assert
    assert deployment == deployment1


def test_deployment_id_in_db_is_same_as_in_python(
    sqlite_store: components.SqliteStore,
) -> None:
    """Test that the deployment_id in the db is the same as in python."""
    # Arrange
    now = datetime.datetime.now()
    deployment = data.Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        name="test_device",
    )

    # Act
    sqlite_store.store_deployment(deployment)

    # Assert
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deployment;")
        row = cursor.fetchone()
        assert row["id"] == deployment.id.bytes


def test_recordings_can_be_registered(
    sqlite_store: components.SqliteStore,
    deployment: data.Deployment,
) -> None:
    """Test that recordings can be registered."""
    # Arrange
    now = datetime.datetime.now()
    recording = data.Recording(
        deployment=deployment,
        path=Path("test/path"),
        duration=10.0,
        samplerate=44100,
        datetime=now,
        audio_channels=2,
    )

    # Act
    sqlite_store.store_recording(recording)

    # Assert
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recording;")
        row = cursor.fetchone()
        assert row["path"] == "test/path"
        assert row["duration_s"] == 10.0
        assert row["audio_channels"] == 2
        assert row["samplerate_hz"] == 44100
        assert row["datetime"] == now.isoformat(sep=" ")
        assert row["id"] == recording.id.bytes


def test_recording_can_be_registered_with_custom_deployment(
    sqlite_store: components.SqliteStore,
):
    """Test that recordings can be registered with a custom deployment."""
    # Arrange
    now = datetime.datetime.now()
    deployment = data.Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        name="test_device",
    )
    sqlite_store.store_deployment(deployment)
    recording = data.Recording(
        path=Path("test/path"),
        duration=10.0,
        samplerate=44100,
        datetime=now,
        deployment=deployment,
    )

    # Act
    sqlite_store.store_recording(recording)

    # Assert
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recording;")
        row = cursor.fetchone()
        assert row["path"] == "test/path"
        assert row["duration_s"] == 10.0
        assert row["samplerate_hz"] == 44100
        assert row["datetime"] == now.isoformat(sep=" ")
        assert row["id"] == recording.id.bytes
        assert row["deployment_id"] == deployment.id.bytes


def test_get_all_recordings(
    sqlite_store: components.SqliteStore,
    deployment: data.Deployment,
):
    """Test that all recordings can be retrieved."""
    # Arrange

    # Create two recordings
    now = datetime.datetime.now()
    recording1 = data.Recording(
        deployment=deployment,
        path=Path("test/path1"),
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    recording2 = data.Recording(
        deployment=deployment,
        path=Path("test/path2"),
        duration=10.0,
        samplerate=44100,
        datetime=now + datetime.timedelta(seconds=10),
    )

    # Add them to the database
    sqlite_store.store_recording(recording1)
    sqlite_store.store_recording(recording2)

    # Act
    recordings, _ = sqlite_store.get_recordings([recording1.id, recording2.id])

    # Assert
    assert len(recordings) == 2
    assert recordings[1] == recording1
    assert recordings[0] == recording2


def test_get_some_recordings(
    sqlite_store: components.SqliteStore,
    deployment: data.Deployment,
):
    """Test that recordings can be retrieved with an include filter."""
    # Arrange

    # Create two recordings
    now = datetime.datetime.now()
    recording1 = data.Recording(
        deployment=deployment,
        path=Path("test/path1"),
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    recording2 = data.Recording(
        deployment=deployment,
        path=Path("test/path2"),
        duration=10.0,
        samplerate=44100,
        datetime=now + datetime.timedelta(seconds=10),
    )

    # Add them to the database
    sqlite_store.store_recording(recording1)
    sqlite_store.store_recording(recording2)

    # Act
    recordings, _ = sqlite_store.get_recordings([recording1.id])

    # Assert
    assert len(recordings) == 1
    assert recordings[0] == recording1


def test_can_store_model_outputs(
    sqlite_store: components.SqliteStore,
    model_output: data.ModelOutput,
):
    sqlite_store.store_model_output(model_output)
    db_path = sqlite_store.db_path

    _, retrieved = sqlite_store.get_recordings([model_output.recording.id])
    assert len(retrieved) == 1
    assert retrieved[0][0] == model_output

    # Check that the detections were stored
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM model_output;")
        assert len(cursor.fetchall()) == 1

        cursor.execute("SELECT id FROM detection;")
        assert len(cursor.fetchall()) == 1
