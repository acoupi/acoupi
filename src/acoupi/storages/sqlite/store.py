"""Module defining the SqliteStore class"""
from typing import List

from pony import orm

from acoupi.storages.sqlite.database import create_database
from acoupi.types import Deployment, Detection, Recording, Store


class SqliteStore(Store):
    """Sqlite store implementation"""

    def __init__(self, db_path: str) -> None:
        """Initialise the Sqlite Store.

        Will create a database file at the given path if it does not exist.

        Args:
            db_path: Path to the database file

        """
        self.db_path = db_path
        self.db, self.models = create_database()
        self.db.bind(provider="sqlite", filename=db_path, create_db=True)
        self.db.generate_mapping(create_tables=True)

    def get_current_deployment(self) -> Deployment:
        """Get the current deployment"""
        return Deployment()

    def store_deployment(self, deployment: Deployment) -> None:
        """Store the deployment locally"""
        pass

    @orm.db_session
    def store_recording(self, recording: Recording) -> None:
        """Store the recording locally"""
        self.models.Recording(
            path=recording.path,
            duration_s=recording.duration,
            samplerate_hz=recording.samplerate,
            channels=1,
            datetime=recording.datetime,
            deployment=recording.deployment,
        )
        orm.commit()


    def store_detections(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> None:
        """Store the detection locally"""
        pass
