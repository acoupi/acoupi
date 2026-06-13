"""SQLite message-store query helpers."""

import sqlite3
import datetime
from typing import List
from uuid import UUID

from acoupi import data
from acoupi.system.exceptions import MessageStoreError


def store_message(
    connection: sqlite3.Connection,
    message: data.Message,
    content: bytes,
) -> None:
    connection.execute(
        "INSERT INTO message (id, content, created_on) VALUES (?, ?, ?)",
        (
            message.id.bytes,
            content,
            serialise_datetime(message.created_on),
        ),
    )


def get_unsent_messages(connection: sqlite3.Connection) -> List[data.Message]:
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
            created_on=parse_datetime(row["created_on"]),
        )
        for row in rows
    ]


def store_response(
    connection: sqlite3.Connection,
    response: data.Response,
) -> None:
    row = connection.execute(
        "SELECT 1 FROM message WHERE id = ?",
        (response.message.id.bytes,),
    ).fetchone()
    if row is None:
        raise MessageStoreError(
            f"Cannot store response for unknown message {response.message.id}."
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
            serialise_datetime(response.received_on),
        ),
    )


def serialise_datetime(value: data.AwareDatetime) -> str:
    return value.isoformat(sep=" ")


def parse_datetime(value: str) -> data.AwareDatetime:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed
