"""Module defining the SqliteStore class."""
import datetime
from typing import List, Optional
from uuid import UUID

from pony import orm

from storages.sqlite import types as db_types
from storages.sqlite.database import create_base_models
from acoupi_types import Deployment, Detection, Recording, Store
import acoupi_utils as utils
#from acoupi import utils
#from acoupi.storages.sqlite import types as db_types
#from acoupi.storages.sqlite.database import create_base_models
#from acoupi.types import Deployment, Detection, Recording, Store


class SqliteStore(Store):
    """Sqlite store implementation.

    The store is used to store the recordings, detections and deployments
    locally. The data is stored in a sqlite database file in the given path.

    Under the hood, the store uses the Pony ORM to interact with the database.
    The database schema is defined in the database module and contains the
    following tables:

    - Deployment: Contains the deployment information. Each deployment is
      associated with a device, and has a start datetime. The deployment can
      also have a latitude and longitude associated with it.

    - Recording: Contains the recording information. Each recording is
      associated with a deployment, and has a datetime, duration, samplerate
      and number of channels.

    - Detection: Contains the detection information. Each detection is
      associated with a recording, and has a species name and a probability.

    The store is thread-safe, and can be used from multiple threads
    simultaneously.

    Attributes:
        db_path: Path to the database file. Can be set to :memory: to use an
            in-memory database.

        database: The Pony ORM database object.

        models: The Pony ORM models.

    """

    db_path: str
    """Path to the database file."""

    database: orm.Database
    """The Pony ORM database object."""

    models: db_types.BaseModels
    """The Pony ORM models."""

    def __init__(self, db_path: str) -> None:
        """Initialise the Sqlite Store.

        Will create a database file at the given path if it does not exist.

        Args:
            db_path: Path to the database file. Can be set to :memory: to use
                an in-memory database.

        """
        self.db_path = db_path
        self.database = orm.Database()
        self.models = create_base_models(self.database)
        self.database.bind(provider="sqlite", filename=db_path, create_db=True)
        self.database.generate_mapping(create_tables=True)

    @orm.db_session
    def get_current_deployment(self) -> Deployment:
        """Get the current deployment.

        The current deployment is the one with the latest started_on datetime.

        If no deployment is found, a new deployment will be registered with the
        current datetime, and the latitude and longitude set to None.

        Returns:
            The current deployment
        """
        deployment = self._get_current_deployment()
        return Deployment(
            id=deployment.id,
            started_on=deployment.started_on,
            device_id=deployment.device_id,
            name=deployment.name,
            latitude=deployment.latitude,
            longitude=deployment.longitude,
        )

    @orm.db_session
    def store_deployment(self, deployment: Deployment) -> None:
        """Store the deployment locally.

        Args:
            deployment: The deployment to store
        """
        self._get_or_create_deployment(deployment)

    @orm.db_session
    def store_recording(
        self,
        recording: Recording,
        deployment: Optional[Deployment] = None,
    ) -> None:
        """Store the recording locally.

        If the deployment is not provided, the current deployment will be used.

        Args:
            recording: The recording to store
            deployment: The deployment associated with the recording
        """
        self._get_or_create_recording(recording, deployment)

    @orm.db_session
    def store_detections(
        self,
        recording: Recording,
        detections: List[Detection],
        deployment: Optional[Deployment] = None,
    ) -> None:
        """Store the detection locally.

        Save all the provided detections to the local database. Provide the
        recording associated with the detections.

        If the recording has not been stored yet, it will be created. In this
        case, you can also provide the deployment associated with the
        recording, otherwise the current deployment will be used.

        Args:
            recording: The recording associated with the detections.
            detections: The detections to store.
            deployment: The deployment associated with the recording. Only
                provide if the recording has not been stored yet and you do not
                want to use the current deployment.
        """
        recording_db = self._get_or_create_recording(
            recording,
            deployment=deployment,
        )

        for detection in detections:
            self._create_detection(detection, recording_db)

    @orm.db_session
    def get_recordings(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[Recording]:
        """Get the recordings from the local filesystem.

        Args:
            include: A list of recording IDs to include. If None, all
                recordings are included.
            exclude: A list of recording IDs to exclude. If None, no
                recordings are excluded. Can not be used simultaneously
                with include.

        Returns:
            A list of recordings.
        """
        if exclude is not None and include is not None:
            raise ValueError("Can not use both include and exclude.")

        recordings = self.models.Recording.select()

        if include is not None:
            recordings = recordings.filter(lambda r: r.id in include)

        if exclude is not None:
            recordings = recordings.filter(lambda r: r.id not in exclude)

        return [
            Recording(
                id=recording.id,
                path=recording.path,
                datetime=recording.datetime,
                duration=recording.duration_s,
                samplerate=recording.samplerate_hz,
            )
            for recording in recordings
        ]

    @orm.db_session
    def get_detections(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[Detection]:
        """Get the detections from the local filesystem.

        Args:
            include: A list of detection IDs to include. If None, all
                detections are included.
            exclude: A list of detection IDs to exclude. If None, no
                detections are excluded. Can not be used simultaneously
                with include.

        Returns:
            A list of detections.
        """
        if exclude is not None and include is not None:
            raise ValueError("Can not use both include and exclude.")

        detections = self.models.Detection.select()

        if include is not None:
            detections = detections.filter(lambda d: d.id in include)

        if exclude is not None:
            detections = detections.filter(lambda d: d.id not in exclude)

        return [
            Detection(
                id=detection.id,
                species_name=detection.species_name,
                class_probability=detection.class_probability,
                soundevent_probability=detection.soundevent_probability
            )
            for detection in detections
        ]

    @orm.db_session
    def get_deployments(
        self,
        include: Optional[List[UUID]] = None,
        exclude: Optional[List[UUID]] = None,
    ) -> List[Deployment]:
        """Get the deployments from the local filesystem.

        Args:
            include: A list of deployment IDs to include. If None, all
                deployments are included.
            exclude: A list of deployment IDs to exclude. If None, no
                deployments are excluded. Can not be used simultaneously
                with include.

        Returns:
            A list of deployments.
        """
        if exclude is not None and include is not None:
            raise ValueError("Can not use both include and exclude.")

        deployments = self.models.Deployment.select()

        if include is not None:
            deployments = deployments.filter(lambda d: d.id in include)

        if exclude is not None:
            deployments = deployments.filter(lambda d: d.id not in exclude)

        return [
            Deployment(
                id=deployment.id,
                started_on=deployment.started_on,
                device_id=deployment.device_id,
                name=deployment.name,
                latitude=deployment.latitude,
                longitude=deployment.longitude,
            )
            for deployment in deployments
        ]

    @orm.db_session
    def _get_current_deployment(self) -> db_types.Deployment:
        """Get the current deployment in the database."""
        db_deployment = (
            orm.select(d for d in self.models.Deployment)
            .order_by(orm.desc(self.models.Deployment.started_on))
            .first()
        )

        if db_deployment is None:
            # TODO: Think better about the default values
            db_deployment = self.models.Deployment(
                started_on=datetime.datetime.now(),
                device_id=utils.get_rpi_serial_number(),
                name=utils.get_rpi_host_name(),
                latitude=None,
                longitude=None,
            )
            orm.commit()

        return db_deployment

    @orm.db_session
    def _get_recording_by_datetime(
        self,
        date: datetime.datetime,
    ) -> db_types.Recording:
        """Get the recording by the datetime."""
        recording: Optional[db_types.Recording] = self.models.Recording.get(
            datetime=date
        )  # type: ignore

        if recording is None:
            raise ValueError("No recording found")

        return recording

    @orm.db_session
    def _create_recording(
        self,
        recording: Recording,
        deployment: Optional[Deployment] = None,
    ) -> db_types.Recording:
        """Create a recording."""
        if deployment is None:
            deployment_db = self._get_current_deployment()
        else:
            deployment_db = self._get_or_create_deployment(deployment)

        db_recording = self.models.Recording(
            id=recording.id,
            path=recording.path,
            duration_s=recording.duration,
            samplerate_hz=recording.samplerate,
            channels=recording.channels,
            datetime=recording.datetime,
            deployment=deployment_db,
        )
        orm.commit()
        return db_recording

    @orm.db_session
    def _get_or_create_recording(
        self,
        recording: Recording,
        deployment: Optional[Deployment] = None,
    ) -> db_types.Recording:
        """Get or create a recording."""
        try:
            db_recording = self._get_recording_by_datetime(recording.datetime)
        except ValueError:
            db_recording = self._create_recording(
                recording,
                deployment=deployment,
            )

        return db_recording

    @orm.db_session
    def _get_deployment_by_started_on(
        self, started_on: datetime.datetime
    ) -> db_types.Deployment:
        """Get the deployment by the started_on datetime."""
        deployment: Optional[db_types.Deployment] = self.models.Deployment.get(
            started_on=started_on
        )  # type: ignore

        if deployment is None:
            raise ValueError("No deployment found")

        return deployment

    @orm.db_session
    def _create_deployment(
        self, deployment: Deployment
    ) -> db_types.Deployment:
        """Create a deployment."""
        db_deployment = self.models.Deployment(
            id=deployment.id,
            started_on=deployment.started_on,
            device_id=deployment.device_id,
            name=deployment.name,
            latitude=deployment.latitude,
            longitude=deployment.longitude,
        )
        orm.commit()
        return db_deployment

    def _get_or_create_deployment(
        self, deployment: Deployment
    ) -> db_types.Deployment:
        """Get or create a deployment."""
        try:
            db_deployment = self._get_deployment_by_started_on(
                deployment.started_on
            )
        except ValueError:
            db_deployment = self._create_deployment(deployment)

        return db_deployment

    @orm.db_session
    def _create_detection(
        self,
        detection: Detection,
        db_recording: db_types.Recording,
    ) -> db_types.Detection:
        """Create a detection."""
        db_detection = self.models.Detection(
            id=detection.id,
            recording=db_recording,
            species_name=detection.species_name,
            class_probability=detection.class_probability,
            soundevent_probability=detection.soundevent_probability,
        )
        orm.commit()
        return db_detection
