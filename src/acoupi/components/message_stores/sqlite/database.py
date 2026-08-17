"""Schema helpers for the SQLite message store."""

import sqlite3

SCHEMA_VERSION = 2


def get_db_version(connection: sqlite3.Connection) -> int:
    """Get the current schema version of the database."""
    cursor = connection.execute("PRAGMA user_version;")
    row = cursor.fetchone()
    return row[0] if row else 0


def set_db_version(connection: sqlite3.Connection, version: int) -> None:
    """Set the schema version of the database."""
    connection.execute(f"PRAGMA user_version = {version};")


def apply_add_message_type_migration(connection: sqlite3.Connection) -> None:
    """Add message_type column to message table if missing."""
    cursor = connection.execute("PRAGMA table_info(message);")
    columns = {
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in cursor.fetchall()
    }
    if columns and "message_type" not in columns:
        connection.execute("ALTER TABLE message ADD COLUMN message_type TEXT;")


def migrate_db(
    connection: sqlite3.Connection,
    target_version: int = SCHEMA_VERSION,
) -> None:
    """Migrate the database to the target version."""
    current_version = get_db_version(connection)

    if current_version < 2:
        apply_add_message_type_migration(connection)
        set_db_version(connection, 2)


def create_message_schema(
    connection: sqlite3.Connection,
    version: int = SCHEMA_VERSION,
) -> None:
    """Create the message-store schema if it does not exist and apply migrations."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS message (
            id BLOB PRIMARY KEY,
            content BLOB NOT NULL,
            created_on TEXT NOT NULL,
            message_type TEXT
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
    migrate_db(connection, target_version=version)
