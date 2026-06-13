"""Message store Sqlite implementation."""

from pathlib import Path
from typing import List, Union

from . import queries
from .database import create_message_schema
from acoupi import data
from acoupi.components import types
from acoupi.system.database import connect_db


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

    def __init__(self, db_path: Path) -> None:
        """Initialise the message store."""
        self.db_path = db_path
        with connect_db(self.db_path) as connection:
            create_message_schema(connection)

    def store_message(
        self,
        message: data.Message,
    ) -> None:
        """Register a recording message with the store."""
        with connect_db(self.db_path) as connection:
            queries.store_message(
                connection,
                message,
                self._as_bytes(message.content),
            )

    def get_unsent_messages(self) -> List[data.Message]:
        """Get the messages that have not been synced to the server."""
        with connect_db(self.db_path) as connection:
            return queries.get_unsent_messages(connection)

    def store_response(
        self,
        response: data.Response,
    ) -> None:
        """Store a response to a message."""
        with connect_db(self.db_path) as connection:
            queries.store_response(connection, response)

    @staticmethod
    def _as_bytes(content: Union[str, bytes]) -> bytes:
        """Normalise message content to bytes for storage."""
        if isinstance(content, bytes):
            return content

        return content.encode("utf-8")
