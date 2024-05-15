"""Auxiliary type definitions for message store models."""

from datetime import datetime
from typing import List, NamedTuple
from uuid import UUID

from pony.orm import core


class Message(core.EntityMeta):
    """Message ORM model."""

    id: UUID
    """Unique ID of the message"""

    content: str
    """Message content"""

    created_on: datetime
    """Datetime when the message was created"""

    responses: List["Response"]
    """Responses to the message."""


class Response(core.EntityMeta):
    """Message status ORM model."""

    id: int
    """Unique ID of the message status"""

    status: int
    """Response code of the response"""

    content: str
    """Content of the response"""

    sent_on: datetime
    """Datetime when the message was sent"""

    message: Message
    """Message that the status belongs to"""


class MessageModels(NamedTuple):
    """Container for message models."""

    Message: Message
    Response: Response
