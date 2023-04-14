"""Message store Sqlite implementation."""

from typing import List

from pony import orm

from acoupi import types
from acoupi.storages.sqlite import types as db_types
from acoupi.storages.sqlite.database import create_message_models


class SqliteMessageStore(types.MessageStore):
    """Message store Sqlite implementation.

    This store keeps track of messages that have been sent to a remote server.
    It stores the response of the server and the datetime when the message was
    sent. This allows the client to keep track of which messages have been
    sent and which have not, allowing it to send them again if necessary.

    The messages are stored in a local sqlite database.
    """

    db_path: str
    """Path to the database file."""

    database: orm.Database
    """The Pony ORM database object."""

    models: db_types.MessageModels
    """The Pony ORM models."""

    store: types.Store
    """Access to the local store"""

    def __init__(self, db_path: str, store: types.Store) -> None:
        """Initialize the message store."""
        self.db_path = db_path
        self.database = orm.Database()
        self.models = create_message_models(
            self.database,
        )
        self.database.bind(provider="sqlite", filename=db_path, create_db=True)
        self.database.generate_mapping(create_tables=True)
        self.store = store

    @orm.db_session
    def store_recording_message(
        self,
        recording: types.Recording,
        response: types.Response,
    ) -> None:
        """Register a recording message with the store."""

    @orm.db_session
    def store_deployment_message(
        self,
        deployment: types.Deployment,
        response: types.Response,
    ) -> None:
        """Register a deployment message with the store."""

    @orm.db_session
    def store_detection_message(
        self,
        detection: types.Detection,
        response: types.Response,
    ) -> None:
        """Register a detection message with the store."""

    @orm.db_session
    def get_unsynced_detections(self) -> List[types.Detection]:
        """Get the unsynced detections.

        Returns:
            The unsynced detections
        """
        detections = orm.select(
            d
            for d in self.store.models.Detection
            if not any(
                message.message_status.response_ok
                for message in d.detection_messages
            )
        )
        return [
            types.Detection(
                id=detection.id,
                species_name=detection.species_name,
                probability=detection.probability,
            )
            for detection in detections
        ]

    @orm.db_session
    def get_unsynced_recordings(self) -> List[types.Recording]:
        """Get the unsynced recordings.

        Returns:
            The unsynced recordings
        """
        recordings = orm.select(
            r
            for r in self.store.models.Recording
            if not any(
                message.message_status.response_ok
                for message in r.recording_messages
            )
        )
        return [
            types.Recording(
                id=recording.id,
                path=recording.path,
                datetime=recording.datetime,
                duration=recording.duration_s,
                samplerate=recording.samplerate_hz,
            )
            for recording in recordings
        ]

    @orm.db_session
    def get_unsynced_deployments(self) -> List[types.Deployment]:
        """Get the unsynced deployments.

        Returns:
            The unsynced deployments
        """
        deployments = orm.select(
            d
            for d in self.store.models.Deployment
            if not any(
                message.message_status.response_ok
                for message in d.deployment_messages
            )
        )
        return [
            types.Deployment(
                id=deployment.id,
                started_on=deployment.started_on,
                device_id=deployment.device_id,
                name=deployment.device_name,
                latitude=deployment.latitude,
                longitude=deployment.longitude,
            )
            for deployment in deployments
        ]
