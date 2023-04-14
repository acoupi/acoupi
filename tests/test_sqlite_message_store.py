"""Test the SQLite Message store."""
import datetime
import os
import sqlite3
from pathlib import Path
from typing import Generator, Tuple

import pytest

from acoupi.storages.sqlite.message_store import SqliteMessageStore
from acoupi.storages.sqlite.store import SqliteStore
from acoupi.types import Deployment, Detection, Recording


@pytest.fixture(scope="function")
def sqlite_message_store(
    tmp_path: Path,
) -> Generator[SqliteMessageStore, None, None]:
    """Create a store."""
    db_path = tmp_path / "test.db"
    message_db_path = tmp_path / "message_test.db"
    store = SqliteStore(str(db_path))
    message_store = SqliteMessageStore(str(message_db_path), store)
    yield message_store
    db_path.unlink()


def test_message_status_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the message_status table has the correct columns."""
    expected_columns = {
        "id",
        "response_ok",
        "response_code",
        "sent_on",
    }
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(message_status);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_deployment_message_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the deployment_message table has the correct columns."""
    expected_columns = {"id", "deployment_id", "message_status_id"}
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(deployment_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_recording_message_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the recording_message table has the correct columns."""
    expected_columns = {"id", "recording_id", "message_status_id"}
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recording_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_detection_message_table_has_correct_columns(
    sqlite_message_store,
) -> None:
    """Test that the detection_message table has the correct columns."""
    expected_columns = {"id", "detection_id", "message_status_id"}
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(detection_message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns
