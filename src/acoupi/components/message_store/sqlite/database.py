"""Database models for the acoupi database."""
from datetime import datetime
from uuid import UUID

from pony import orm

from .types import MessageModels


def create_message_models(
    database: orm.Database,
) -> MessageModels:
    """Create the database models."""
    BaseModel = database.Entity

    class Message(BaseModel):  # type: ignore
        _table_ = "message"

        id = orm.PrimaryKey(UUID, auto=True)
        """Unique ID of the message status"""

        content = orm.Required(str)
        """Message content."""

        created_on = orm.Required(datetime)
        """Datetime when the message was created."""

        responses = orm.Set("Response")
        """Responses to the message."""

    class Response(BaseModel):  # type: ignore
        _table_ = "response"

        id = orm.PrimaryKey(int, auto=True)
        """Unique ID of the deployment message"""

        content = orm.Optional(str)
        """Content of the response."""

        message = orm.Required(Message, column="message_id")
        """Message that the status belongs to."""

        status = orm.Required(int)
        """Status of the response."""

        received_on = orm.Required(datetime)
        """Datetime when the response was received."""

    return MessageModels(
        Message=Message,  # type: ignore
        Response=Response,  # type: ignore
    )
