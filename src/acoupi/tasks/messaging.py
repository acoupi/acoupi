"""Messaging Task.

This module contains the function to send messages to a remote server.
The send data task is a function that sends data to a remote server using
a messenger and message store. The send data process send unsynced deployments,
recordings, and detections to the remote server. The process will then store
the response from the remote server, so that the data can be marked as
synced. The send data process contains the following steps:

1. Get the unsent messages from the message store.
2. Send the messages to a remote server.
3. Store the response from the remote server in the message store.
"""

import logging
from typing import Callable, Literal

from acoupi.components import types
from acoupi.system.exceptions import MessageSendError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
MAX_DEBUG_CONTENT_LENGTH = 200


def generate_send_messages_task(
    message_store: types.MessageStore,
    messengers: list[types.Messenger] | None = None,
    max_messages: int | None = None,
    order: Literal["oldest_first", "newest_first"] = "oldest_first",
    logger: logging.Logger = logger,
) -> Callable[[], None]:
    """Generate a send data task.

    Parameters
    ----------
    message_store : types.MessageStore
        The message store to get and store messages.
    messengers : list[types.Messenger] | None, optional
        The messengers to send messages, by default None.
    max_messages : int | None, optional
        Maximum number of messages to send per task run. If `None`, all
        unsent messages are sent.
    order : Literal["oldest_first", "newest_first"], optional
        Order in which unsent messages are selected, by default
        "oldest_first".
    logger : logging.Logger, optional
        The logger to log messages, by default logger.

    Raises
    ------
    ValueError
        Raised if `messengers` is empty or not provided, or if
        `max_messages` is not a positive integer.

    Notes
    -----
    The send data task calls the following methods:

    1. **message_store.get_unsent_messages()** -> List[data.Message]
        - Get the unsent messages from the message store.
        - See [components.message_stores][acoupi.components.message_stores] for implementation of [types.MessageStore][acoupi.components.types.MessageStore].
    2. **messenger.send_message(message)** -> data.Response
        - Send the messages to a remote server.
        - See [acoupi.components.messengers][acoupi.components.messengers] for implementation of [types.Messenger][acoupi.components.types.Messenger].
    3. **message_store.store_response(response)** -> None
        - Store the response from the remote server in the message store.
        - See [components.message_stores][acoupi.components.message_stores] for implementation of [types.MessageStore][acoupi.components.types.MessageStore].
    """
    if not messengers:
        raise ValueError("At least one messenger must be provided.")

    if max_messages is not None and max_messages <= 0:
        raise ValueError("max_messages must be a positive integer or None.")

    def send_messages_task() -> None:
        """Send Messages."""
        logger.info(
            "Starting message send task with %d messenger(s), limit=%s, order=%s.",
            len(messengers),
            max_messages,
            order,
        )
        messages = message_store.get_unsent_messages(
            limit=max_messages,
            order=order,
        )
        logger.info("Selected %d message(s) to be sent.", len(messages))

        attempted_sends = 0
        successful_sends = 0
        failed_sends = 0

        for messenger in messengers:
            for message in messages:
                attempted_sends += 1
                logger.debug(
                    "Sending message %s via %s with content %r.",
                    message.id,
                    messenger.__class__.__name__,
                    _format_message_content_for_debug(message.content),
                )
                try:
                    response = messenger.send_message(message)
                except MessageSendError as error:
                    failed_sends += 1
                    logger.error(
                        "Message send failed for message %s via %s: %s",
                        message.id,
                        messenger.__class__.__name__,
                        error,
                    )
                    continue

                successful_sends += 1
                logger.debug(
                    "Response received for message %s via %s with status %s.",
                    message.id,
                    messenger.__class__.__name__,
                    response.status,
                )
                message_store.store_response(response)

        logger.info(
            "Finished message send task: %d message(s) selected, %d send attempt(s), %d successful response(s), %d failed send(s).",
            len(messages),
            attempted_sends,
            successful_sends,
            failed_sends,
        )

    return send_messages_task


def _format_message_content_for_debug(content: str | bytes) -> str | bytes:
    if isinstance(content, bytes):
        return content[:MAX_DEBUG_CONTENT_LENGTH]

    return content[:MAX_DEBUG_CONTENT_LENGTH]
