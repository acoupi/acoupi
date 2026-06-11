"""Message store Sqlite implementation."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Union
from uuid import UUID

from .database import create_message_schema
from acoupi import data
from acoupi.components import types
from acoupi.system.exceptions import MessageStoreError


class SqliteMessageStore(types.MessageStore):
    """Message store Sqlite implementation.

    This store keeps track of messages that have been sent to a remote server.
    It stores the response of the server and the datetime when the message was
    sent. This allows the client to keep track of which messages have been
    sent and which have not, allowing it to send them again if necessary.

    The messages are stored in a local sqlite database.
    """

    db_path: Path
    """Path to the database file."""

    _memory_connection: sqlite3.Connection | None

    def __init__(self, db_path: Path) -> None:
        """Initialise the message store."""
        self.db_path = db_path
        self._memory_connection = None
        if str(self.db_path) == ":memory:":
            self._memory_connection = self._create_connection()

        with self._connect() as connection:
            create_message_schema(connection)

    def store_message(
        self,
        message: data.Message,
    ) -> None:
        """Register a recording message with the store."""
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO message (id, content, created_on) VALUES (?, ?, ?)",
                (
                    message.id.bytes,
                    self._as_bytes(message.content),
                    _serialise_datetime(message.created_on),
                ),
            )

    def get_unsent_messages(self) -> List[data.Message]:
        """Get the messages that have not been synced to the server."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT m.id, m.content, m.created_on
                FROM message AS m
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM response AS r
                    WHERE r.message_id = m.id AND r.status = ?
                )
                """,
                (data.ResponseStatus.SUCCESS.value,),
            ).fetchall()

        return [
            data.Message(
                id=UUID(bytes=row["id"]),
                content=row["content"],
                created_on=_parse_datetime(row["created_on"]),
            )
            for row in rows
        ]

    def store_response(
        self,
        response: data.Response,
    ) -> None:
        """Store a response to a message."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM message WHERE id = ?",
                (response.message.id.bytes,),
            ).fetchone()
            if row is None:
                raise MessageStoreError(
                    "Cannot store response for unknown message "
                    f"{response.message.id}."
                )

            connection.execute(
                """
                INSERT INTO response (content, message_id, status, received_on)
                VALUES (?, ?, ?, ?)
                """,
                (
                    response.content,
                    response.message.id.bytes,
                    response.status.value,
                    _serialise_datetime(response.received_on),
                ),
            )

    @staticmethod
    def _as_bytes(content: Union[str, bytes]) -> bytes:
        """Normalise message content to bytes for storage."""
        if isinstance(content, bytes):
            return content

        return content.encode("utf-8")

    @contextmanager
    def _connect(self):
        if self._memory_connection is not None:
            yield self._memory_connection
            return

        connection = self._create_connection()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _create_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection


def _serialise_datetime(value: datetime) -> str:
    return value.isoformat(sep=" ")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)
