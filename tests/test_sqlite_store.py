"""Test the SQLite store."""
import os
import sqlite3
import datetime
from pathlib import Path
from typing import Generator

import pytest

from acoupi.types import Recording, Detection
from acoupi.storages.sqlite.store import SqliteStore


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

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_detection_table_has_correct_columns(sqlite_store) -> None:
    """Test that the detection table has the correct columns"""
    expected_columns = {"id", "probability", "species_name", "recording_id"}
    db_path = sqlite_store.db_path

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_table_has_correct_columns(sqlite_store) -> None:
    """Test that the deployment table has the correct columns"""
    expected_columns = {"id", "latitude", "longitude", "device_id"}
    db_path = sqlite_store.db_path

    # Check that the tables are there
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

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(message_status);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_message_table_has_correct_columns(sqlite_store) -> None:
    """Test that the deployment_message table has the correct columns"""
    expected_columns = {"id", "deployment_id", "message_status_id"}
    db_path = sqlite_store.db_path

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(deployment_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_recording_message_table_has_correct_columns(sqlite_store) -> None:
    """Test that the recording_message table has the correct columns"""
    expected_columns = {"id", "recording_id", "message_status_id"}
    db_path = sqlite_store.db_path

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_detection_message_table_has_correct_columns(sqlite_store) -> None:
    """Test that the detection_message table has the correct columns"""
    expected_columns = {"id", "detection_id", "message_status_id"}
    db_path = sqlite_store.db_path

    # Check that the tables are there
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_can_instantiate_multiple_stores_to_the_same_sqlite_file(tmp_path: Path) -> None:
    """Test that we can instantiate multiple stores to the same sqlite file"""
    db_path = tmp_path / "test.db"
    store1 = SqliteStore(str(db_path))
    store2 = SqliteStore(str(db_path))
    assert store1 is not None
    assert store2 is not None


def test_recordings_can_be_registered(sqlite_store: SqliteStore) -> None:
    """Test that recordings can be registered"""
    now = datetime.datetime.now()

    recording = Recording(
        path="test/path",
        duration=10.0,
        samplerate=44100,
        datetime=now,
    )
    sqlite_store.store_recording(recording)

    # Check that the recording is there
    with sqlite3.connect(str(sqlite_store.db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recording;")
        row = cursor.fetchone()
        assert row[1] == "test/path"
        assert row[2] == 10.0
        assert row[3] == 44100
        assert row[4] == 1
        assert row[5] == now.isoformat()

