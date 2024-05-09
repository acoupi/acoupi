"""Module defining the SqliteStore class."""
import datetime
import json
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

from pony import orm

from acoupi import data
from acoupi.components import types

from . import types as db_types
from .database import create_base_models


class SqliteStore(types.Store):
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
      and number of                 audio_channels.

    - PredictedTag: Contains the predicted tag information. Each predicted tag
      has a key, value and probability.

    - Detection: Contains the detection information. Each detection consists
      of a location, probability and a list of predicted tags.

    - ModelOutput: Contains the model output information. Each model output
      has the model name, the list of predicted tags at the recording level,
      and a list of detections.

    The store is thread-safe, and can be used from multiple threads
    simultaneously.
    """

    db_path: Path
    """Path to the database file."""

    database: orm.Database
    """The Pony ORM database object."""

    models: db_types.BaseModels
    """The Pony ORM models."""

    def __init__(self, db_path: Path) -> None:
        """Initialise the Sqlite Store.

        Will create a database file at the given path if it does not exist.

        Args:
            db_path: Path to the database file. Can be set to :memory: to use
                an in-memory database.
        """
        self.db_path = db_path
        self.database = orm.Database()
        self.models = create_base_models(self.database)
        self.database.bind(
            provider="sqlite",
            filename=str(db_path),
            create_db=True,
        )
        self.database.generate_mapping(create_tables=True)

    @orm.db_session
    def get_current_deployment(self) -> data.Deployment:
        """Get the current deployment.

        The current deployment is the one with the latest started_on datetime.

        If no deployment is found, a new deployment will be registered with the
        current datetime, and the latitude and longitude set to None.

        Returns:
            The current deployment
        """
        deployment = self._get_current_deployment()
        return data.Deployment(
            id=deployment.id,
            name=deployment.name,
            latitude=deployment.latitude,
            longitude=deployment.longitude,
            started_on=deployment.started_on,
        )

    @orm.db_session
    def store_deployment(self, deployment: data.Deployment) -> None:
        """Store the deployment locally.

        Args:
            deployment: The deployment to store
        """
        self._get_or_create_deployment(deployment)

    @orm.db_session
    def store_recording(self, recording: data.Recording) -> None:
        """Store the recording locally.

        If the deployment is not provided, the current deployment will be used.

        Args:
            recording: The recording to store
        """
        self._get_or_create_recording(recording)

    @orm.db_session
    def store_model_output(self, model_output: data.ModelOutput) -> None:
        """Store the model output locally."""
        db_recording = self._get_or_create_recording(model_output.recording)

        db_model_output = self.models.ModelOutput(
            id=model_output.id,
            model_name=model_output.name_model,
            recording=db_recording,
            created_on=model_output.created_on,
        )

        for tag in model_output.tags:
            db_model_output.tags.create(
                key=tag.tag.key,
                value=tag.tag.value,
                classification_probability=tag.classification_probability,
            )

        for detection in model_output.detections:
            location = (
                ""
                if detection.location is None
                else detection.location.model_dump_json()
            )
            db_detection = db_model_output.detections.create(
                id=detection.id,
                location=location,
                detection_probability=detection.detection_probability,
            )

            for tag in detection.tags:
                db_detection.tags.create(
                    key=tag.tag.key,
                    value=tag.tag.value,
                    classification_probability=tag.classification_probability,
                )

        orm.commit()

    @orm.db_session
    def get_recordings_by_path(
        self,
        paths: List[Path],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        """Get a list of recordings from the store by their paths.

        Args:
            paths: The paths of the recordings to get.

        Returns:
            List of tuples of the recording and the corresponding model outputs.
        """
        paths_str = [str(path) for path in paths]
        db_recordings = (
            orm.select(r for r in self.models.Recording if r.path in paths_str)
            .order_by(orm.desc(self.models.Recording.datetime))
            .prefetch(
                self.models.Recording.deployment,
                self.models.Recording.model_outputs,
                self.models.ModelOutput.tags,
                self.models.ModelOutput.detections,
                self.models.Detection.tags,
            )
        )
        return _to_recordings_and_outputs(db_recordings)

    @orm.db_session
    def get_recordings(
        self,
        ids: List[UUID],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        """Get a list recordings from the store by their ids.

        Each recording is returned with the full list of model outputs
        registered.

        Args:
            ids: The ids of the recordings to get.

        Returns:
            A list of tuples of the recording and the model outputs.
        """
        db_recordings = (
            orm.select(r for r in self.models.Recording if r.id in ids)
            .order_by(orm.desc(self.models.Recording.datetime))
            .prefetch(
                self.models.Recording.deployment,
                self.models.Recording.model_outputs,
                self.models.ModelOutput.tags,
                self.models.ModelOutput.detections,
                self.models.Detection.tags,
            )
        )

        return _to_recordings_and_outputs(db_recordings)

    @orm.db_session
    def update_recording_path(
        self,
        recording: data.Recording,
        path: Path,
    ) -> data.Recording:
        """Update the path of a recording.

        Args:
            recording: The recording to update.
            path: The new path.
        """
        db_recording = self._get_or_create_recording(recording)
        db_recording.path = str(path)
        orm.commit()
        recording.path = path
        return recording

    @orm.db_session
    def _get_current_deployment(self) -> db_types.Deployment:
        """Get the current deployment in the database."""
        db_deployment = (
            orm.select(d for d in self.models.Deployment)
            .order_by(orm.desc(self.models.Deployment.started_on))
            .first()
        )

        if db_deployment is None:
            now = datetime.datetime.now()
            name = f'Deployment {now.strftime("%Y-%m-%d %H:%M:%S")}'
            db_deployment = self.models.Deployment(
                started_on=now,
                name=name,
                latitude=None,
                longitude=None,
            )
            orm.commit()

        return db_deployment

    @orm.db_session
    def _create_recording(
        self,
        recording: data.Recording,
    ) -> db_types.Recording:
        """Create a recording."""
        deployment_db = self._get_or_create_deployment(recording.deployment)
        db_recording = self.models.Recording(
            id=recording.id,
            path=str(recording.path),
            duration_s=recording.duration,
            samplerate_hz=recording.samplerate,
            audio_channels=recording.audio_channels,
            datetime=recording.datetime,
            deployment=deployment_db,
        )
        orm.commit()
        return db_recording

    @orm.db_session
    def _get_or_create_recording(
        self,
        recording: data.Recording,
    ) -> db_types.Recording:
        """Get or create a recording."""
        try:
            return self._get_recording_by_id(recording.id)
        except ValueError:
            return self._create_recording(recording)

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
        self,
        deployment: data.Deployment,
    ) -> db_types.Deployment:
        """Create a deployment."""
        db_deployment = self.models.Deployment(
            id=deployment.id,
            started_on=deployment.started_on,
            name=deployment.name,
            latitude=deployment.latitude,
            longitude=deployment.longitude,
        )
        orm.commit()
        return db_deployment

    @orm.db_session
    def _get_or_create_deployment(
        self, deployment: data.Deployment
    ) -> db_types.Deployment:
        """Get or create a deployment."""
        try:
            db_deployment = self._get_deployment_by_id(deployment.id)
        except ValueError:
            db_deployment = self._create_deployment(deployment)

        return db_deployment

    @orm.db_session
    def _get_deployment_by_id(self, id: UUID) -> db_types.Deployment:
        """Get the deployment by the id."""
        deployment: Optional[db_types.Deployment] = self.models.Deployment.get(
            id=id
        )

        if deployment is None:
            raise ValueError("No deployment found")

        return deployment

    @orm.db_session
    def _get_recording_by_id(self, id: UUID) -> db_types.Recording:
        """Get the recording by the id."""
        recording: Optional[db_types.Recording] = self.models.Recording.get(
            id=id
        )

        if recording is None:
            raise ValueError("No recording found")

        return recording


def _to_deployment(db_deployment: db_types.Deployment) -> data.Deployment:
    return data.Deployment(
        id=db_deployment.id,
        name=db_deployment.name,
        latitude=db_deployment.latitude,
        longitude=db_deployment.longitude,
        started_on=db_deployment.started_on,
    )


def _to_recording(db_recording: db_types.Recording) -> data.Recording:
    deployment = _to_deployment(db_recording.deployment)
    return data.Recording(
        id=db_recording.id,
        deployment=deployment,
        datetime=db_recording.datetime,
        duration=db_recording.duration_s,
        samplerate=db_recording.samplerate_hz,
        audio_channels=db_recording.audio_channels,
        path=None if db_recording.path is None else Path(db_recording.path),
    )


def _to_detection(db_detection: db_types.Detection) -> data.Detection:
    location = (
        None
        if db_detection.location == ""
        else json.loads(str(db_detection.location))
    )
    return data.Detection(
        id=db_detection.id,
        location=location,
        detection_probability=db_detection.detection_probability,
        tags=[
            data.PredictedTag(
                tag=data.Tag(
                    key=db_tag.key,
                    value=db_tag.value,
                ),
                classification_probability=db_tag.classification_probability,
            )
            for db_tag in db_detection.tags
        ],
    )


def _to_model_output(
    db_model_output: db_types.ModelOutput,
) -> data.ModelOutput:
    recording = _to_recording(db_model_output.recording)
    return data.ModelOutput(
        id=db_model_output.id,
        name_model=db_model_output.model_name,
        recording=recording,
        created_on=db_model_output.created_on,
        tags=[
            data.PredictedTag(
                tag=data.Tag(
                    key=db_tag.key,
                    value=db_tag.value,
                ),
                classification_probability=db_tag.classification_probability,
            )
            for db_tag in db_model_output.tags
        ],
        detections=[
            _to_detection(db_detection)
            for db_detection in db_model_output.detections
        ],
    )


def _to_recordings_and_outputs(
    db_recordings,
) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
    ret = []
    for db_recording in db_recordings:
        recording = _to_recording(db_recording)

        outputs = []
        for db_model_output in db_recording.model_outputs:
            model_output = _to_model_output(db_model_output)
            outputs.append(model_output)

        ret.append((recording, outputs))

    return ret
