"""Module to Clean the Database."""

from pathlib import Path

from pony import orm

from . import types as db_types
from .database import create_base_models


class SqliteCleaner:
    """Database cleaner."""

    db_path: Path
    """Path to the database file."""

    database: orm.Database
    """The Pony ORM database object."""

    models: db_types.BaseModels
    """The Pony ORM models."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the DbCleaner."""
        self.db_path = db_path
        self.database = orm.Database()
        self.models = create_base_models(self.database)
        self.database.bind(
            provider="sqlite",
            filename=str(db_path),
            create_db=False,  # Do not create the database
        )
        self.database.generate_mapping()

    @orm.db_session
    def delete_db_tables(self) -> None:
        """Delete all tables in the database."""
        with orm.db_session:
            self.database.drop_all_tables(with_all_data=True)

    @orm.db_session
    def clean_db(self) -> None:
        """Clean the database by deleting all tables."""
        self.delete_db_tables()


# db_path = sqlite.SqliteCleaner()
# db_path = sqlite.SqliteCleaner(db_path=config.DEFAULT_DB_PATH)
# db_path = (Path.home() / "acoupi" / "src" / "acoupi" / "components" / "stores" / "sqlite")


def delete_db_tables(db_path: str) -> None:
    """Delete all tables in the database at the given path."""
    cleaner = SqliteCleaner(Path(db_path))
    cleaner.clean_db()


# if __name__ == "__main__":
#     delete_db_tables(db_path)
