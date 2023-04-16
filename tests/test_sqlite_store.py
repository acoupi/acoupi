"""Test the SQLite store."""
import datetime
import os
import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from acoupi.storages.sqlite.store import SqliteStore
from acoupi.types import Deployment, Detection, Recording


@pytest.fixture(scope="function")
def sqlite_store(tmp_path: Path) -> Generator[SqliteStore, None, None]:
    """Create a store."""
    db_path = tmp_path / "test.db"
    yield SqliteStore(str(db_path))
    db_path.unlink()


def test_sqlite_store_creates_a_database_file(sqlite_store) -> None:
    """Test that the store creates a database file."""
    db_path = sqlite_store.db_path
    assert os.path.isfile(db_path)


def test_database_has_correct_tables(sqlite_store) -> None:
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


def test_recording_table_has_correct_columns(sqlite_store) -> None:
    """Test that the recording table has the correct columns."""
    expected_columns = {
        "id",
        "path",
        "duration_s",
        "samplerate_hz",
        "channels",
        "datetime",
        "deployment_id",
    }
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_detection_table_has_correct_columns(sqlite_store) -> None:
    """Test that the detection table has the correct columns."""
    expected_columns = {"id", "probability", "species_name", "recording_id"}
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_table_has_correct_columns(sqlite_store) -> None:
    """Test that the deployment table has the correct columns."""
    expected_columns = {
        "id",
        "started_on",
        "latitude",
        "longitude",
        "device_id",
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
    store1 = SqliteStore(str(db_path))
    store2 = SqliteStore(str(db_path))

    # Assert
    assert store1 is not None
    assert store2 is not None


def test_can_store_a_deployment(sqlite_store: SqliteStore) -> None:
    """Test that we can store a deployment."""
    # Arrange
    now = datetime.datetime.now()
    deployment = Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
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
        assert row["device_id"] == "test_device"


def test_get_current_deployment_returns_new_if_no_deployment_exists(
    sqlite_store: SqliteStore,
    patched_rpi_serial_number: str,
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
    assert deployment.device_id == patched_rpi_serial_number
    assert deployment.started_on == now


def test_get_current_deployment_gets_latest_deployment(
    sqlite_store: SqliteStore,
) -> None:
    """Test that get_current_deployment gets the latest deployment."""
    # Arrange
    start_1 = datetime.datetime.now()
    start_2 = datetime.datetime.now() - datetime.timedelta(days=10)
    deployment1 = Deployment(
        started_on=start_1,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
        name="test_device",
    )
    deployment2 = Deployment(
        started_on=start_2,
        latitude=3.0,
        longitude=4.0,
        device_id="test_device",
        name="test_device",
    )
    sqlite_store.store_deployment(deployment1)
    sqlite_store.store_deployment(deployment2)

    # Act
    deployment = sqlite_store.get_current_deployment()

    # Assert
    assert deployment == deployment1


def test_deployment_id_in_db_is_same_as_in_python(
    sqlite_store: SqliteStore,
) -> None:
    """Test that the deployment_id in the db is the same as in python."""
    # Arrange
    now = datetime.datetime.now()
    deployment = Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
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
    sqlite_store: SqliteStore,
    patched_rpi_serial_number: str,
) -> None:
    """Test that recordings can be registered."""
    # Arrange
    now = datetime.datetime.now()
    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
        channels=2,
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
        assert row["channels"] == 2
        assert row["samplerate_hz"] == 44100
        assert row["datetime"] == now.isoformat(sep=" ")
        assert row["id"] == recording.id.bytes


def test_recording_can_be_registered_with_custom_deployment(
    sqlite_store: SqliteStore,
):
    """Test that recordings can be registered with a custom deployment."""
    # Arrange
    now = datetime.datetime.now()
    deployment = Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
        name="test_device",
    )
    sqlite_store.store_deployment(deployment)
    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )

    # Act
    sqlite_store.store_recording(recording, deployment=deployment)

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


def test_detections_can_be_stored_with_unregistered_recording(
    sqlite_store: SqliteStore,
    patched_rpi_serial_number: str,
):
    """Test that detections can be registered"""
    # Arrange
    now = datetime.datetime.now()
    detection = Detection(
        species_name="test_species",
        probability=0.5,
    )
    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    # Make sure there are no recordings
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recording;")

    # Act
    sqlite_store.store_detections(recording, [detection])

    # Assert

    # The detection should be stored
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection;")
        row = cursor.fetchone()
        assert row["species_name"] == "test_species"
        assert row["probability"] == 0.5
        assert row["id"] == detection.id.bytes
        assert row["recording_id"] == recording.id.bytes

    # The recording should be stored as well
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


def test_detections_can_be_stored_with_registered_recording(
    sqlite_store: SqliteStore,
    patched_rpi_serial_number: str,
):
    """Test that detections can be registered"""
    # Arrange
    now = datetime.datetime.now()
    detection = Detection(
        species_name="test_species",
        probability=0.5,
    )
    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    sqlite_store.store_recording(recording)

    # Act
    sqlite_store.store_detections(recording, [detection])

    # Assert
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection;")
        row = cursor.fetchone()
        assert row["species_name"] == "test_species"
        assert row["probability"] == 0.5
        assert row["id"] == detection.id.bytes
        assert row["recording_id"] == recording.id.bytes


def test_multiple_detections_can_be_stored_at_once(
    sqlite_store: SqliteStore,
    patched_rpi_serial_number: str,
):
    """Test that multiple detections can be registered at once"""
    # Arrange
    now = datetime.datetime.now()
    detection1 = Detection(
        species_name="test_species1",
        probability=0.5,
    )
    detection2 = Detection(
        species_name="test_species2",
        probability=0.7,
    )
    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    sqlite_store.store_recording(recording)

    # Act
    sqlite_store.store_detections(recording, [detection1, detection2])

    # Assert
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection;")
        row = cursor.fetchone()
        assert row["species_name"] == "test_species1"
        assert row["probability"] == 0.5
        assert row["id"] == detection1.id.bytes
        assert row["recording_id"] == recording.id.bytes
        row = cursor.fetchone()
        assert row["species_name"] == "test_species2"
        assert row["probability"] == 0.7
        assert row["id"] == detection2.id.bytes
        assert row["recording_id"] == recording.id.bytes


def test_get_all_recordings(sqlite_store, patched_rpi_serial_number):
    """Test that all recordings can be retrieved."""
    # Arrange

    # Create two recordings
    now = datetime.datetime.now()
    recording1 = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    recording2 = Recording(
        path="test/path2",
        duration=10.0,
        samplerate=44100,
        datetime=now + datetime.timedelta(seconds=10),
    )

    # Add them to the database
    sqlite_store.store_recording(recording1)
    sqlite_store.store_recording(recording2)

    # Act
    recordings = sqlite_store.get_recordings()

    # Assert
    assert len(recordings) == 2
    assert recordings[0] == recording1
    assert recordings[1] == recording2


def test_get_recordings_with_include(sqlite_store, patched_rpi_serial_number):
    """Test that recordings can be retrieved with an include filter."""
    # Arrange

    # Create two recordings
    now = datetime.datetime.now()
    recording1 = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    recording2 = Recording(
        path="test/path2",
        duration=10.0,
        samplerate=44100,
        datetime=now + datetime.timedelta(seconds=10),
    )

    # Add them to the database
    sqlite_store.store_recording(recording1)
    sqlite_store.store_recording(recording2)

    # Act
    recordings = sqlite_store.get_recordings(include=[recording1.id])

    # Assert
    assert len(recordings) == 1
    assert recordings[0] == recording1


def test_get_recordings_with_exclude(sqlite_store, patched_rpi_serial_number):
    """Test that recordings can be retrieved with an include filter."""
    # Arrange

    # Create two recordings
    now = datetime.datetime.now()
    recording1 = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    recording2 = Recording(
        path="test/path2",
        duration=10.0,
        samplerate=44100,
        datetime=now + datetime.timedelta(seconds=10),
    )

    # Add them to the database
    sqlite_store.store_recording(recording1)
    sqlite_store.store_recording(recording2)

    # Act
    recordings = sqlite_store.get_recordings(exclude=[recording1.id])

    # Assert
    assert len(recordings) == 1
    assert recordings[0] == recording2


def test_get_recordings_with_include_and_exclude(
    sqlite_store,
    patched_rpi_serial_number,
):
    """Test that get_recordings raises if both include and exclude are used."""
    # Arrange

    # Create two recordings
    now = datetime.datetime.now()
    recording1 = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    recording2 = Recording(
        path="test/path2",
        duration=10.0,
        samplerate=44100,
        datetime=now + datetime.timedelta(seconds=10),
    )

    # Add them to the database
    sqlite_store.store_recording(recording1)
    sqlite_store.store_recording(recording2)

    # Act
    with pytest.raises(ValueError):
        sqlite_store.get_recordings(
            include=[recording1.id], exclude=[recording2.id]
        )


def test_get_all_deployments(sqlite_store):
    """Test that all deployments can be retrieved."""
    # Arrange

    # Create two deployments
    now = datetime.datetime.now()
    deployment1 = Deployment(
        started_on=now,
        device_id="test_device_id1",
        name="test_deployment1",
    )
    deployment2 = Deployment(
        started_on=now + datetime.timedelta(seconds=10),
        device_id="test_device_id1",
        name="test_deployment2",
    )

    # Add them to the database
    sqlite_store.store_deployment(deployment1)
    sqlite_store.store_deployment(deployment2)

    # Act
    deployments = sqlite_store.get_deployments()

    # Assert
    assert len(deployments) == 2
    assert deployments[0] == deployment1
    assert deployments[1] == deployment2


def test_get_deployments_with_exclude(sqlite_store):
    """Test that deployments can be retrieved with an exclude filter."""
    # Arrange

    # Create two deployments
    now = datetime.datetime.now()
    deployment1 = Deployment(
        started_on=now,
        device_id="test_device_id1",
        name="test_deployment1",
    )
    deployment2 = Deployment(
        started_on=now + datetime.timedelta(seconds=10),
        device_id="test_device_id1",
        name="test_deployment2",
    )

    # Add them to the database
    sqlite_store.store_deployment(deployment1)
    sqlite_store.store_deployment(deployment2)

    # Act
    deployments = sqlite_store.get_deployments(exclude=[deployment1.id])

    # Assert
    assert len(deployments) == 1
    assert deployments[0] == deployment2


def test_get_deployment_with_include(sqlite_store):
    """Test that deployments can be retrieved with an include filter."""
    # Arrange

    # Create two deployments
    now = datetime.datetime.now()
    deployment1 = Deployment(
        started_on=now,
        device_id="test_device_id1",
        name="test_deployment1",
    )
    deployment2 = Deployment(
        started_on=now + datetime.timedelta(seconds=10),
        device_id="test_device_id1",
        name="test_deployment2",
    )

    # Add them to the database
    sqlite_store.store_deployment(deployment1)
    sqlite_store.store_deployment(deployment2)

    # Act
    deployments = sqlite_store.get_deployments(include=[deployment1.id])

    # Assert
    assert len(deployments) == 1
    assert deployments[0] == deployment1


def test_get_deployments_with_include_and_exclude(sqlite_store):
    """Test that get_deployments raises if both include and exclude are used."""
    # Arrange

    # Create two deployments
    now = datetime.datetime.now()
    deployment1 = Deployment(
        started_on=now,
        device_id="test_device_id1",
        name="test_deployment1",
    )
    deployment2 = Deployment(
        started_on=now + datetime.timedelta(seconds=10),
        device_id="test_device_id1",
        name="test_deployment2",
    )

    # Add them to the database
    sqlite_store.store_deployment(deployment1)
    sqlite_store.store_deployment(deployment2)

    # Act
    with pytest.raises(ValueError):
        sqlite_store.get_deployments(
            include=[deployment1.id], exclude=[deployment2.id]
        )


def test_get_all_detections(sqlite_store, patched_rpi_serial_number):
    """Test that all detections can be retrieved."""
    # Arrange

    # Create a recording
    now = datetime.datetime.now()

    recording = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )

    detection1 = Detection(
        species_name="test_species_name1",
        probability=0.5,
    )
    detection2 = Detection(
        species_name="test_species_name2",
        probability=0.6,
    )

    # Add them to the database
    sqlite_store.store_recording(recording)
    sqlite_store.store_detections(recording, [detection1, detection2])

    # Act
    detections = sqlite_store.get_detections()

    # Assert
    assert len(detections) == 2
    assert detections[0] == detection1
    assert detections[1] == detection2


def test_get_detections_with_exclude(sqlite_store, patched_rpi_serial_number):
    """Test that detections can be retrieved with an exclude filter."""
    # Arrange

    # Create a recording
    now = datetime.datetime.now()

    recording = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )

    detection1 = Detection(
        species_name="test_species_name1",
        probability=0.5,
    )
    detection2 = Detection(
        species_name="test_species_name2",
        probability=0.6,
    )

    # Add them to the database
    sqlite_store.store_recording(recording)
    sqlite_store.store_detections(recording, [detection1, detection2])

    # Act
    detections = sqlite_store.get_detections(exclude=[detection1.id])

    # Assert
    assert len(detections) == 1
    assert detections[0] == detection2


def test_get_detections_with_include(sqlite_store, patched_rpi_serial_number):
    """Test that detections can be retrieved with an include filter."""
    # Arrange

    # Create a recording
    now = datetime.datetime.now()

    recording = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )

    detection1 = Detection(
        species_name="test_species_name1",
        probability=0.5,
    )
    detection2 = Detection(
        species_name="test_species_name2",
        probability=0.6,
    )

    # Add them to the database
    sqlite_store.store_recording(recording)
    sqlite_store.store_detections(recording, [detection1, detection2])

    # Act
    detections = sqlite_store.get_detections(include=[detection1.id])

    # Assert
    assert len(detections) == 1
    assert detections[0] == detection1


def test_get_detections_with_exclude_and_include(
    sqlite_store, patched_rpi_serial_number
):
    """Test that get_detections raises if both include and exclude are used."""
    # Arrange

    # Create a recording
    now = datetime.datetime.now()

    recording = Recording(
        path="test/path1",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )

    detection1 = Detection(
        species_name="test_species_name1",
        probability=0.5,
    )
    detection2 = Detection(
        species_name="test_species_name2",
        probability=0.6,
    )

    # Add them to the database
    sqlite_store.store_recording(recording)
    sqlite_store.store_detections(recording, [detection1, detection2])

    # Act
    with pytest.raises(ValueError):
        sqlite_store.get_detections(
            include=[detection1.id], exclude=[detection2.id]
        )
