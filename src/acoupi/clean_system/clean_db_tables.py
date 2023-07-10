"""Module to Clean the Database"""
from pathlib import Path
from acoupi.components.stores import sqlite
from acoupi import config
import sys

db_path = sqlite.SqliteCleaner(db_path=config.DEFAULT_DB_PATH)
db_path = Path.home()/"acoupi"/"src"/"acoupi"/"components"/"stores"/"sqlite"


def delete_db_tables(db_path: str) -> None:
    """Delete all tables in the database at the given path."""
    cleaner = SqliteCleaner(Path(db_path))
    cleaner.clean_db()

if __name__ == "__main__":
    delete_db_tables(db_path)
