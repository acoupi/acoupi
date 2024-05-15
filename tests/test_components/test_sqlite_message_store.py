"""Test the SQLite Message store."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from acoupi import components, data


@pytest.fixture(scope="function")
def sqlite_message_store(
    tmp_path: Path,
) -> Generator[components.SqliteMessageStore, None, None]:
    """Create a store."""
    message_db_path = tmp_path / "message_test.db"
    message_store = components.SqliteMessageStore(message_db_path)
    yield message_store
    message_db_path.unlink()


def test_message_table_has_correct_columns(
    sqlite_message_store: components.SqliteMessageStore,
) -> None:
    """Test that the message_status table has the correct columns."""
    expected_columns = {
        "id",
        "content",
        "created_on",
    }
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(message);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_response_table_has_correct_columns(
    sqlite_message_store: components.SqliteMessageStore,
) -> None:
    """Test that the message_status table has the correct columns."""
    expected_columns = {
        "id",
        "content",
        "message_id",
        "status",
        "received_on",
    }
    db_path = sqlite_message_store.db_path

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(response);")
        actual_columns = set(row[1] for row in cursor.fetchall())
        assert expected_columns == actual_columns


def test_store_message(
    sqlite_message_store: components.SqliteMessageStore,
):
    """Test storing a message."""
    # Arrange
    message = data.Message(content="test message")

    # Act
    sqlite_message_store.store_message(message)

    # Assert
    # Make sure the message was stored in the database
    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM message;")
        row = cursor.fetchone()
        assert row[1] == "test message"
        assert row[0] == message.id.bytes


def test_store_response(
    sqlite_message_store: components.SqliteMessageStore,
):
    """Test storing a response."""
    # Arrange
    message = data.Message(content="test message")
    response = data.Response(
        content="test response",
        status=data.ResponseStatus.SUCCESS,
        message=message,
    )

    # Act
    sqlite_message_store.store_response(response)

    # Assert
    # Make sure the response was stored in the database
    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM response;")
        row = cursor.fetchone()
        assert row[1] == "test response"
        assert row[2] == message.id.bytes
        assert row[3] == data.ResponseStatus.SUCCESS.value
        assert row[4] is not None


def test_get_unsent_messages(
    sqlite_message_store: components.SqliteMessageStore,
):
    """Test getting unsent messages."""
    # Arrange
    message1 = data.Message(content="test message 1")
    message2 = data.Message(content="test message 2")
    message3 = data.Message(content="test message 3")
    response1 = data.Response(
        content="test response 1",
        status=data.ResponseStatus.SUCCESS,
        message=message1,
    )
    response2 = data.Response(
        content="test response 2",
        status=data.ResponseStatus.FAILED,
        message=message2,
    )

    # Act
    sqlite_message_store.store_message(message1)
    sqlite_message_store.store_message(message2)
    sqlite_message_store.store_message(message3)
    sqlite_message_store.store_response(response1)
    sqlite_message_store.store_response(response2)
    unsent_messages = sqlite_message_store.get_unsent_messages()

    # Assert
    assert len(unsent_messages) == 2
