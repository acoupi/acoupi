"""Module defining the SqliteStore class."""

import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from acoupi import data
from acoupi.components import types
from acoupi.components.stores.sqlite import queries
from acoupi.components.stores.sqlite.database import create_base_schema
from acoupi.system.database import connect_db
from acoupi.system.exceptions import MetadataStoreError


class SqliteStore(types.Store):
    """Sqlite store implementation.

    The store is used to store the recordings, detections and deployments
    locally. The data is stored in a sqlite database file in the given path.

    The database schema is defined in the database module and contains the
    following tables:

    - Deployment: Contains the deployment information. Each deployment is
      associated with a device, and has a start datetime. The deployment can
      also have a latitude and longitude associated with it.

    - Recording: Contains the recording information. Each recording is
      associated with a deployment, and has a datetime, duration, samplerate
      and number of                 audio_channels.

    - PredictedTag: Contains the predicted tag information. Each predicted tag
      has a key, value and score.

    - Detection: Contains the detection information. Each detection consists
      of a prediction type, location, score and a list of predicted tags.

    - ModelOutput: Contains the model output information. Each model output
      has the model name and a list of detections.

    The store is thread-safe, and can be used from multiple threads
    simultaneously.

    Notes
    -----
    The ID of the deployment, recording, model output and detection is a UUID
    field. Note that sqlite stores UUIDs as a BLOB, so when querying the
    database with SQL, you should use the hex function to convert the UUID to a string.

    Example queries:

    .. code-block:: sql

        -- Find a specific deployment by UUID
        SELECT * FROM Deployment WHERE hex(id) = '00000000000000000000000000000000';

        -- Get all deployment UUIDs as strings
        SELECT hex(id) FROM Deployment;
    """

    db_path: Path
    """Path to the database file."""

    def __init__(self, db_path: Path) -> None:
        """Initialise the Sqlite Store.

        Will create a database file at the given path if it does not exist.

        Args:
            db_path: Path to the database file. Can be set to :memory: to use
                an in-memory database.
        """
        self.db_path = db_path

        with connect_db(self.db_path) as connection:
            create_base_schema(connection)

    def get_current_deployment(self) -> data.Deployment:
        """Get the current deployment.

        The current deployment is the one with the latest started_on datetime.

        If no deployment is found, a new deployment will be registered with the
        current datetime, and the latitude and longitude set to None.

        Returns
        -------
            The current deployment
        """
        with connect_db(self.db_path) as connection:
            deployment = queries.get_current_deployment(connection)

            if deployment is not None:
                return deployment

            now = datetime.datetime.now()
            deployment = data.Deployment(
                started_on=now,
                name=f"Deployment {now.strftime('%Y-%m-%d %H:%M:%S')}",
                latitude=None,
                longitude=None,
            )
            queries.create_deployment(connection, deployment)
            return deployment

    def store_deployment(self, deployment: data.Deployment) -> None:
        """Store the deployment locally.

        Args:
            deployment: The deployment to store
        """
        with connect_db(self.db_path) as connection:
            try:
                queries.get_deployment_by_id(connection, deployment.id)
            except ValueError:
                queries.create_deployment(connection, deployment)

    def update_deployment(self, deployment: data.Deployment) -> None:
        with connect_db(self.db_path) as connection:
            queries.update_deployment(connection, deployment)

    def store_recording(
        self,
        recording: data.Recording,
        deployment: Optional[data.Deployment] = None,
    ) -> None:
        """Store the recording locally.

        Args:
            recording: The recording to store
        """
        if deployment is not None:
            recording = recording.model_copy(
                update=dict(deployment=deployment)
            )

        with connect_db(self.db_path) as connection:
            existing = queries.get_recordings_by_ids(
                connection, [recording.id]
            )

            if existing:
                return

            try:
                deployment = queries.get_deployment_by_id(
                    connection,
                    recording.deployment.id,
                )
            except ValueError:
                deployment = queries.create_deployment(
                    connection,
                    recording.deployment,
                )

            queries.create_recording(connection, recording, deployment)

    def store_model_output(self, model_output: data.ModelOutput) -> None:
        """Store the model output locally."""
        self.store_model_outputs([model_output])

    def store_model_outputs(
        self,
        model_outputs: List[data.ModelOutput],
    ) -> None:
        """Store multiple model outputs locally using bulk sqlite inserts."""
        if not model_outputs:
            return

        self._ensure_recordings_exist(model_outputs)

        with connect_db(self.db_path) as connection:
            queries.insert_model_outputs(connection, model_outputs)

    def get_recordings_by_path(
        self,
        paths: Sequence[Optional[Path]],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        """Get a list of recordings from the store by their paths.

        Args:
            paths: The paths of the recordings to get.

        Returns
        -------
            List of tuples of the recording and the corresponding model outputs.
        """
        paths_str = [str(path) for path in paths if path is not None]
        if not paths_str:
            return []

        with connect_db(self.db_path) as connection:
            recordings = queries.get_recordings_by_paths(connection, paths_str)
        outputs_by_recording_id = self.get_recordings_model_outputs(recordings)
        return [
            (recording, outputs_by_recording_id.get(recording.id, []))
            for recording in recordings
        ]

    def get_recordings_info_by_path(
        self,
        paths: Sequence[Optional[Path]],
    ) -> List[Tuple[data.Recording, List[data.ModelOutputInfo]]]:
        """Get recordings by path with lightweight model-output metadata."""
        paths_str = [str(path) for path in paths if path is not None]
        if not paths_str:
            return []

        with connect_db(self.db_path) as connection:
            recordings = queries.get_recordings_by_paths(connection, paths_str)
            outputs_by_recording_id = queries.get_recordings_model_output_info(
                connection,
                [recording.id for recording in recordings],
            )
        return [
            (recording, outputs_by_recording_id.get(recording.id, []))
            for recording in recordings
        ]

    def get_recording_model_outputs(
        self,
        recording: data.Recording,
    ) -> List[data.ModelOutput]:
        """Get full model outputs associated with a single recording."""
        return self.get_recordings_model_outputs([recording]).get(
            recording.id, []
        )

    def get_recordings_model_outputs(
        self,
        recordings: Sequence[data.Recording],
    ) -> Dict[UUID, List[data.ModelOutput]]:
        """Get full model outputs associated with multiple recordings."""
        if not recordings:
            return {}

        recordings_by_id = {
            recording.id: recording for recording in recordings
        }
        recording_ids = list(recordings_by_id)
        with connect_db(self.db_path) as connection:
            outputs_by_recording_id = queries.get_recordings_model_outputs(
                connection,
                recordings_by_id,
            )
            if not outputs_by_recording_id:
                return {recording_id: [] for recording_id in recording_ids}

        for recording_id in recording_ids:
            outputs_by_recording_id.setdefault(recording_id, [])
        return outputs_by_recording_id

    def get_recordings(
        self,
        ids: List[UUID],
    ) -> List[Tuple[data.Recording, List[data.ModelOutput]]]:
        """Get a list recordings from the store by their ids.

        Each recording is returned with the full list of model outputs
        registered.

        Args:
            ids: The ids of the recordings to get.

        Returns
        -------
            A list of tuples of the recording and the model outputs.
        """
        with connect_db(self.db_path) as connection:
            recordings = queries.get_recordings_by_ids(connection, ids)
        outputs_by_recording_id = self.get_recordings_model_outputs(recordings)
        return [
            (recording, outputs_by_recording_id.get(recording.id, []))
            for recording in recordings
        ]

    def get_model_outputs(
        self,
        after: Optional[datetime.datetime] = None,
        before: Optional[datetime.datetime] = None,
        ids: Optional[List[UUID]] = None,
        recording_ids: Optional[List[UUID]] = None,
        model_names: Optional[List[str]] = None,
        detection_ids: Optional[List[UUID]] = None,
        limit: Optional[int] = None,
    ) -> List[data.ModelOutput]:
        """Get a list of model outputs from the store by their id.

        Args:
            start_time: The time to start the search from.
            end_time: The time to end the search at.

        Returns
        -------
            List of model_outputs matching the created_on datetime.
        """
        with connect_db(self.db_path) as connection:
            return queries.get_model_outputs(
                connection,
                after=after,
                before=before,
                ids=ids,
                recording_ids=recording_ids,
                model_names=model_names,
                detection_ids=detection_ids,
                limit=limit,
            )

    def get_detections(
        self,
        ids: Optional[List[UUID]] = None,
        model_output_ids: Optional[List[UUID]] = None,
        score_gt: Optional[float] = None,
        score_lt: Optional[float] = None,
        model_names: Optional[List[str]] = None,
        after: Optional[datetime.datetime] = None,
        before: Optional[datetime.datetime] = None,
    ) -> List[data.Detection]:
        """Get a list of detections from the store based on their model_output ids."""
        with connect_db(self.db_path) as connection:
            return queries.get_detections(
                connection,
                ids=ids,
                model_output_ids=model_output_ids,
                score_gt=score_gt,
                score_lt=score_lt,
                model_names=model_names,
                after=after,
                before=before,
            )

    def get_predicted_tags(
        self,
        detection_ids: Optional[List[UUID]] = None,
        after: Optional[datetime.datetime] = None,
        before: Optional[datetime.datetime] = None,
        score_gt: Optional[float] = None,
        score_lt: Optional[float] = None,
        keys: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
    ) -> List[data.PredictedTag]:
        """Get a list of predicted tags from the store based on their detection ids."""
        with connect_db(self.db_path) as connection:
            return queries.get_predicted_tags(
                connection,
                detection_ids=detection_ids,
                after=after,
                before=before,
                score_gt=score_gt,
                score_lt=score_lt,
                keys=keys,
                values=values,
            )

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
        with connect_db(self.db_path) as connection:
            queries.update_recording_path(connection, recording.id, path)
        return recording.model_copy(update=dict(path=path))

    def _ensure_recordings_exist(
        self,
        model_outputs: List[data.ModelOutput],
    ) -> None:
        """Ensure all recordings referenced by model outputs exist."""
        recordings_by_id = {}

        for model_output in model_outputs:
            recording = model_output.recording
            recordings_by_id[recording.id] = recording

        recording_ids = list(recordings_by_id)
        with connect_db(self.db_path) as connection:
            existing_recording_ids = queries.get_existing_recording_ids(
                connection,
                recording_ids,
            )

        missing_recordings = [
            recording
            for recording_id, recording in recordings_by_id.items()
            if recording_id not in existing_recording_ids
        ]

        if missing_recordings:
            missing_descriptions = []
            for recording in missing_recordings:
                path = (
                    "no path"
                    if recording.path is None
                    else str(recording.path)
                )
                missing_descriptions.append(f"id={recording.id}, path={path}")
            raise MetadataStoreError(
                "Cannot store model outputs because the following recordings "
                "are not present in the metadata store: "
                + "; ".join(missing_descriptions)
                + ". Store the recordings first with store_recording()."
            )
