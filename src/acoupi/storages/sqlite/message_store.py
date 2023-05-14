"""Message store Sqlite implementation."""

from typing import List

from pony import orm

import acoupi_types as types
from storages.sqlite import types as db_types
from storages.sqlite.database import create_message_models
#from acoupi import types
#from acoupi.storages.sqlite import types as db_types
#from acoupi.storages.sqlite.database import create_message_models


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
        self.models = create_message_models(self.database)
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
        status = self.models.MessageStatus(
            response_ok=response.status == types.ResponseStatus.SUCCESS,
            response_code=response.status.value,
            sent_on=response.message.sent_on,
        )

        self.models.RecordingMessage(
            recording_id=recording.id,
            message_status=status,
        )

        orm.commit()

    @orm.db_session
    def store_deployment_message(
        self,
        deployment: types.Deployment,
        response: types.Response,
    ) -> None:
        """Register a deployment message with the store."""
        status = self.models.MessageStatus(
            response_ok=response.status == types.ResponseStatus.SUCCESS,
            response_code=response.status.value,
            sent_on=response.message.sent_on,
        )

        self.models.DeploymentMessage(
            deployment_id=deployment.id,
            message_status=status,
        )

        orm.commit()

    @orm.db_session
    def store_detection_message(
        self,
        detection: types.Detection,
        response: types.Response,
    ) -> None:
        """Register a detection message with the store."""
        status = self.models.MessageStatus(
            response_ok=response.status == types.ResponseStatus.SUCCESS,
            response_code=response.status.value,
            sent_on=response.message.sent_on,
        )

        self.models.DetectionMessage(
            detection_id=detection.id,
            message_status=status,
        )

        orm.commit()

    @orm.db_session
    def get_unsynced_detections(self) -> List[types.Detection]:
        """Get the unsynced detections.

        Returns:
            The unsynced detections
        """
        synced_detections = [
            detection_id
            for detection_id in orm.select(
                m.detection_id
                for m in self.models.DetectionMessage
                if m.message_status.response_ok
            )
        ]

        return self.store.get_detections(exclude=synced_detections)

    @orm.db_session
    def get_unsynced_recordings(self) -> List[types.Recording]:
        """Get the unsynced recordings.

        Returns:
            The unsynced recordings
        """
        synced_recordings = [
            recording_id
            for recording_id in orm.select(
                m.recording_id
                for m in self.models.RecordingMessage
                if m.message_status.response_ok
            )
        ]

        return self.store.get_recordings(exclude=synced_recordings)

    @orm.db_session
    def get_unsynced_deployments(self) -> List[types.Deployment]:
        """Get the unsynced deployments.

        Returns:
            The unsynced deployments
        """
        synced_deployments = [
            deployment_id
            for deployment_id in orm.select(
                m.deployment_id
                for m in self.models.DeploymentMessage
                if m.message_status.response_ok
            )
        ]

        return self.store.get_deployments(exclude=synced_deployments)
