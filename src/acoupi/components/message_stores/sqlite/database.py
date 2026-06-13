"""Schema helpers for the SQLite message store."""

import sqlite3


def create_message_schema(connection: sqlite3.Connection) -> None:
    """Create the message-store schema if it does not exist."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS message (
            id BLOB PRIMARY KEY,
            content BLOB NOT NULL,
            created_on TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS response (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            message_id BLOB NOT NULL,
            status INTEGER NOT NULL,
            received_on TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES message(id)
        );

        CREATE INDEX IF NOT EXISTS idx_response_message_id
        ON response(message_id);

        CREATE INDEX IF NOT EXISTS idx_response_status
        ON response(status);
        """
    )
