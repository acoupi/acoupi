from pathlib import Path
from pony import orm
import datetime

db_path = "bat1_acoupi_102023.db"

database = orm.Database()
database.bind(provider="sqlite", filename=str(db_path), create_db=False)

# database = SqliteStore(db_path)
# deployment = database.get_current_deployment()
# print(deployment)


def get_daily_summary(database):
    with orm.db_session:
        daily_summary = database.select(
            "select count(*), value, avg(probability) from predicted_tag group by value"
        )
        return daily_summary


daily_summary = get_daily_summary(database)
print(daily_summary)
# print(detection_id)
# print()
