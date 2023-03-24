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
    """Create a store"""
    db_path = tmp_path / "test.db"
    yield SqliteStore(str(db_path))
    db_path.unlink()


def test_sqlite_store_creates_a_database_file(sqlite_store) -> None:
    """Test that the store creates a database file"""
    db_path = sqlite_store.db_path
    assert os.path.isfile(db_path)


def test_database_has_correct_tables(sqlite_store) -> None:
    """Test that the database has the correct tables"""
    expected_tables = {
        "recording",
        "deployment",
        "detection",
        "message_status",
        "deployment_message",
        "recording_message",
        "detection_message",
    }
    db_path = sqlite_store.db_path

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        actual_tables = set(row[0] for row in cursor.fetchall())
        assert expected_tables.issubset(actual_tables)


def test_recording_table_has_correct_columns(sqlite_store) -> None:
    """Test that the recording table has the correct columns"""
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
    """Test that the detection table has the correct columns"""
    expected_columns = {"id", "probability", "species_name", "recording_id"}
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_table_has_correct_columns(sqlite_store) -> None:
    """Test that the deployment table has the correct columns"""
    expected_columns = {
        "id",
        "started_on",
        "latitude",
        "longitude",
        "device_id",
    }
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(deployment);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_message_status_table_has_correct_columns(sqlite_store) -> None:
    """Test that the message_status table has the correct columns"""
    expected_columns = {
        "id",
        "response_ok",
        "response_code",
        "sent_on",
    }
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(message_status);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_message_table_has_correct_columns(sqlite_store) -> None:
    """Test that the deployment_message table has the correct columns"""
    expected_columns = {"id", "deployment_id", "message_status_id"}
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(deployment_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_recording_message_table_has_correct_columns(sqlite_store) -> None:
    """Test that the recording_message table has the correct columns"""
    expected_columns = {"id", "recording_id", "message_status_id"}
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_detection_message_table_has_correct_columns(sqlite_store) -> None:
    """Test that the detection_message table has the correct columns"""
    expected_columns = {"id", "detection_id", "message_status_id"}
    db_path = sqlite_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_can_instantiate_multiple_stores_with_the_same_sqlite_file(
    tmp_path: Path,
) -> None:
    """Test that we can instantiate multiple stores to the same sqlite file"""
    # Arrange
    db_path = tmp_path / "test.db"

    # Act
    store1 = SqliteStore(str(db_path))
    store2 = SqliteStore(str(db_path))

    # Assert
    assert store1 is not None
    assert store2 is not None


def test_can_store_a_deployment(sqlite_store: SqliteStore) -> None:
    """Test that we can store a deployment"""
    # Arrange
    now = datetime.datetime.now()
    deployment = Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
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
    """Test that get_current_deployment fails if no deployment exists"""
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
    """Test that get_current_deployment gets the latest deployment"""
    # Arrange
    start_1 = datetime.datetime.now()
    start_2 = datetime.datetime.now() - datetime.timedelta(days=10)
    deployment1 = Deployment(
        started_on=start_1,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
    )
    deployment2 = Deployment(
        started_on=start_2,
        latitude=3.0,
        longitude=4.0,
        device_id="test_device",
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
    """Test that the deployment_id in the db is the same as in python"""
    # Arrange
    now = datetime.datetime.now()
    deployment = Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
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
    """Test that recordings can be registered"""
    # Arrange
    now = datetime.datetime.now()
    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
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


def test_recording_can_be_registered_with_custom_deployment(
    sqlite_store: SqliteStore,
):
    """Test that recordings can be registered with a custom deployment"""
    # Arrange
    now = datetime.datetime.now()
    deployment = Deployment(
        started_on=now,
        latitude=1.0,
        longitude=2.0,
        device_id="test_device",
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
