import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


def create_connection(path: Path | str) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


@contextmanager
def connect_db(path: Path | str) -> Generator[sqlite3.Connection, None, None]:
    connection = create_connection(path)

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
