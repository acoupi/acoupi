"""Module defining the SqliteStore class"""
import datetime
from typing import List, Optional

from pony import orm

from acoupi.storages.sqlite import types as db_types
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

    @orm.db_session
    def _get_deployment_by_started_on(self, started_on: datetime.datetime):
        """Get the deployment by the started_on datetime"""
        deployment = self.models.Deployment.get(started_on=started_on)

        if deployment is None:
            raise ValueError("No deployment found")

        return deployment

    @orm.db_session
    def get_current_deployment(self) -> Deployment:
        """Get the current deployment"""
        deployment = (
            orm.select(d for d in self.models.Deployment)
            .order_by(orm.desc(self.models.Deployment.started_on))
            .first()
        )

        if deployment is None:
            raise ValueError("No deployment found")

        return Deployment(
            started_on=deployment.started_on,
            device_id=deployment.device_id,
            latitude=deployment.latitude,
            longitude=deployment.longitude,
        )

    @orm.db_session
    def store_deployment(self, deployment: Deployment) -> None:
        """Store the deployment locally"""
        self.models.Deployment(
            started_on=deployment.started_on,
            device_id=deployment.device_id,
            latitude=deployment.latitude,
            longitude=deployment.longitude,
        )
        orm.commit()

    @orm.db_session
    def store_recording(
        self,
        recording: Recording,
        deployment: Optional[Deployment] = None,
    ) -> None:
        """Store the recording locally"""
        if deployment is None:
            deployment_db = self.get_current_deployment()
        else:
            deployment_db = self._get_deployment_by_started_on(
                deployment.started_on
            )

        self.models.Recording(
            path=recording.path,
            duration_s=recording.duration,
            samplerate_hz=recording.samplerate,
            channels=1,
            datetime=recording.datetime,
            deployment=deployment_db,
        )
        orm.commit()

    def store_detections(
        self,
        recording: Recording,
        detections: List[Detection],
    ) -> None:
        """Store the detection locally"""
        pass
