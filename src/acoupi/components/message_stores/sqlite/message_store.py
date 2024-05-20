"""Message store Sqlite implementation."""

from pathlib import Path
from typing import List

from pony import orm

from . import types as db_types
from .database import create_message_models
from acoupi import data
from acoupi.components import types


class SqliteMessageStore(types.MessageStore):
    """Message store Sqlite implementation.

    This store keeps track of messages that have been sent to a remote server.
    It stores the response of the server and the datetime when the message was
    sent. This allows the client to keep track of which messages have been
    sent and which have not, allowing it to send them again if necessary.

    The messages are stored in a local sqlite database.
    """

    db_path: Path
    """Path to the database file."""

    database: orm.Database
    """The Pony ORM database object."""

    models: db_types.MessageModels
    """The Pony ORM models."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the message store."""
        self.db_path = db_path
        self.database = orm.Database()
        self.models = create_message_models(self.database)
        self.database.bind(
            provider="sqlite",
            filename=str(db_path),
            create_db=True,
        )
        self.database.generate_mapping(create_tables=True)

    @orm.db_session
    def store_message(
        self,
        message: data.Message,
    ) -> None:
        """Register a recording message with the store."""
        return self._create_message(message)

    @orm.db_session
    def get_unsent_messages(self) -> List[data.Message]:
        """Get the messages that have not been synced to the server."""
        # Get messages that haven't had an OK response
        unsent_messages = self.models.Message.select(
            lambda m: not orm.exists(r for r in m.responses if r.status == 0)
        )

        return [
            data.Message(
                id=message.id,
                content=message.content,
                created_on=message.created_on,
            )
            for message in unsent_messages
        ]

    @orm.db_session
    def store_response(
        self,
        response: data.Response,
    ) -> None:
        """Store a response to a message."""
        try:
            db_message = self.models.Message[response.message.id]
        except orm.ObjectNotFound:
            db_message = self._create_message(response.message)

        self.models.Response(
            message=db_message,
            content=response.content or "",
            status=response.status.value,
            received_on=response.received_on,
        )
        orm.commit()

    @orm.db_session
    def _create_message(
        self,
        message: data.Message,
    ) -> db_types.Message:
        """Create a Pony ORM message object."""
        db_message = self.models.Message(
            id=message.id,
            content=message.content,
            created_on=message.created_on,
        )
        orm.commit()
        return db_message
