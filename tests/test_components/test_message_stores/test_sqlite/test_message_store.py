"""Test the SQLite Message store."""

import datetime
import shutil
import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from acoupi import components, data
from acoupi.system.exceptions import MessageStoreError


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
        "message_type",
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
        assert row[1] == b"test message"
        assert row[0] == message.id.bytes


def test_store_message_bytes(
    sqlite_message_store: components.SqliteMessageStore,
):
    """Test storing a byte message."""
    message = data.Message(content=b"\x01\x02test")

    sqlite_message_store.store_message(message)

    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM message;")
        row = cursor.fetchone()
        assert row[1] == b"\x01\x02test"
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
    sqlite_message_store.store_message(message)
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


def test_store_response_raises_for_missing_message(
    sqlite_message_store: components.SqliteMessageStore,
):
    """Test storing a response fails if the message is not stored."""
    message = data.Message(content=b"\x01\x02payload")
    response = data.Response(
        content="test response",
        status=data.ResponseStatus.SUCCESS,
        message=message,
    )

    with pytest.raises(MessageStoreError, match="unknown message"):
        sqlite_message_store.store_response(response)


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
    assert {message.content for message in unsent_messages} == {
        b"test message 2",
        b"test message 3",
    }


def test_get_unsent_messages_applies_limit_and_oldest_first_order(
    sqlite_message_store: components.SqliteMessageStore,
):
    messages = [
        data.Message(
            content=f"test message {index}",
            created_on=datetime.datetime(
                2024, 1, index, tzinfo=datetime.timezone.utc
            ),
        )
        for index in range(1, 4)
    ]

    for message in messages:
        sqlite_message_store.store_message(message)

    unsent_messages = sqlite_message_store.get_unsent_messages(limit=2)

    assert [message.content for message in unsent_messages] == [
        b"test message 1",
        b"test message 2",
    ]


def test_get_unsent_messages_applies_newest_first_order(
    sqlite_message_store: components.SqliteMessageStore,
):
    messages = [
        data.Message(
            content=f"test message {index}",
            created_on=datetime.datetime(
                2024, 1, index, tzinfo=datetime.timezone.utc
            ),
        )
        for index in range(1, 4)
    ]

    for message in messages:
        sqlite_message_store.store_message(message)

    unsent_messages = sqlite_message_store.get_unsent_messages(
        limit=2,
        order="newest_first",
    )

    assert [message.content for message in unsent_messages] == [
        b"test message 3",
        b"test message 2",
    ]


def test_store_message_with_message_type(
    sqlite_message_store: components.SqliteMessageStore,
):
    """Test storing a message with message_type."""
    message = data.Message(
        content="test message",
        message_type=data.MessageType.DETECTION,
    )
    sqlite_message_store.store_message(message)

    db_path = sqlite_message_store.db_path
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_type FROM message;")
        row = cursor.fetchone()
        assert row[0] == "detection"

    unsent = sqlite_message_store.get_unsent_messages()
    assert len(unsent) == 1
    assert unsent[0].message_type == data.MessageType.DETECTION


def test_migrate_db_adds_message_type_column_and_updates_version(
    tmp_path: Path,
):
    """Test migrating an older message store database schema from a snapshot fixture."""
    fixture_path = (
        Path(__file__).resolve().parents[3]
        / "fixtures"
        / "databases"
        / "message_store_v1.db"
    )
    db_path = tmp_path / "migrated_message_store.db"
    shutil.copy2(fixture_path, db_path)

    # Initialise SqliteMessageStore which triggers migration
    store = components.SqliteMessageStore(db_path)

    # Verify migration applied and PRAGMA user_version updated
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version;")
        assert cursor.fetchone()[0] == 2

        cursor.execute("PRAGMA table_info(message);")
        columns = {row[1] for row in cursor.fetchall()}
        assert "message_type" in columns

    # Verify historical unsent messages are readable with message_type=None
    unsent = store.get_unsent_messages()
    assert len(unsent) == 2
    assert {message.content for message in unsent} == {
        b"unsent legacy message 1",
        b"failed legacy message 3",
    }
    assert all(message.message_type is None for message in unsent)

    # Verify new message with message_type can be stored and retrieved
    new_message = data.Message(
        content="new message",
        message_type=data.MessageType.HEARTBEAT,
    )
    store.store_message(new_message)

    unsent = store.get_unsent_messages()
    assert len(unsent) == 3
    heartbeat_msg = [m for m in unsent if m.content == b"new message"][0]
    assert heartbeat_msg.message_type == data.MessageType.HEARTBEAT
