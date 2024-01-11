from pathlib import Path
from pony import orm
import datetime

db_path = "bat1_acoupi_102023.db"

database = orm.Database()
database.bind(provider="sqlite", filename=str(db_path), create_db=False)


def get_daily_summary(database):
    # datetime = datetime.datetime.now()
    day_datetime = datetime.datetime.date("2023-09-29")

    with orm.db_session:
        daily_summary = database.select(
            "select count(value) from predicted_tag where value = 'Pipistrellus pipistrellus'"
        )
        daily_summary = database.select(
            "select count(*) from predicted_tag group by value"
        )
        daily_summary = database.select(
            "select count(*) from predicted_tag group by value where date = day_datetime"
        )
        return daily_summary


daily_summary = get_daily_summary(database)
print(daily_summary)


##


class DailySummaryDBContent:
    """A MdbContent that contains the daily summary of the database."""

    db_path: Path

    database: orm.Database

    def __init__(self, db_path: Path):
        """Initialize the DailySummaryDBContent."""
        self.db_path = db_path
        self.database = orm.Database()
        self.database.bind(
            provider="sqlite",
            filename=str(self.db_path),
            create_db=False,
        )

    def get_daily_summary(self):
        with orm.db_session:
            daily_summary = self.database.select(
                "select count(*) from predicted_tag group by value"
            )
            return daily_summary
