"""Message store Sqlite implementation."""

from pathlib import Path
from typing import Literal

from acoupi import data
from acoupi.components import types
from acoupi.components.message_stores.sqlite import queries
from acoupi.components.message_stores.sqlite.database import (
    create_message_schema,
)
from acoupi.components.message_stores.sqlite.queries import (
    get_unsent_messages as query_get_unsent_messages,
)
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

    def get_unsent_messages(
        self,
        limit: int | None = None,
        order: Literal["oldest_first", "newest_first"] = "oldest_first",
    ) -> list[data.Message]:
        """Get messages that do not have a successful response.

        Parameters
        ----------
        limit : int | None, optional
            Maximum number of unsent messages to return. If `None`, all
            unsent messages are returned.
        order : {"oldest_first", "newest_first"}, optional
            Chooses whether older or newer messages are considered first.
            This matters most when `limit` is set, because it decides which
            messages are returned first. When `limit` is `None`, all unsent
            messages are still returned in the chosen order.

        Returns
        -------
        list[data.Message]
            Messages that still need to be sent, ready to be processed in the
            requested order.
        """
        with connect_db(self.db_path) as connection:
            return query_get_unsent_messages(
                connection,
                limit=limit,
                order=order,
            )

    def store_response(
        self,
        response: data.Response,
    ) -> None:
        """Store the result of sending a message.

        Parameters
        ----------
        response : data.Response
            Result returned after trying to send a message.
        """
        with connect_db(self.db_path) as connection:
            queries.store_response(connection, response)

    @staticmethod
    def _as_bytes(content: str | bytes) -> bytes:
        if isinstance(content, bytes):
            return content

        return content.encode("utf-8")
