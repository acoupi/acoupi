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
    """Generate a task that sends queued messages.

    The returned task retrieves unsent messages from ``message_store``,
    applies the requested selection order and optional limit, sends the
    selected messages with each messenger, and stores successful
    responses.

    Parameters
    ----------
    message_store : types.MessageStore
        Message store used to retrieve unsent messages and persist
        responses.
    messengers : list[types.Messenger] | None, optional
        Messenger instances used to send the selected messages. Must
        contain at least one messenger.
    max_messages : int | None, optional
        Maximum number of messages to send per task run. If `None`, all
        unsent messages are sent.
    order : Literal["oldest_first", "newest_first"], optional
        Order used to prioritise which unsent messages are selected first.
    logger : logging.Logger, optional
        Logger instance used to report task progress and send outcomes.

    Returns
    -------
    Callable[[], None]
        A task that sends the selected messages when called.

    Raises
    ------
    ValueError
        Raised if `messengers` is empty or not provided, or if
        `max_messages` is not a positive integer.

    Notes
    -----
    When ``max_messages`` is ``None``, the task selects all unsent
    messages. Otherwise, it selects at most ``max_messages`` messages
    using ``order`` to determine which messages are considered first.
    """
    if not messengers:
        raise ValueError("At least one messenger must be provided.")

    if max_messages is not None and max_messages <= 0:
        raise ValueError("max_messages must be a positive integer or None.")

    def send_messages_task() -> None:
        """Send Messages."""
        logger.info(
            (
                "Starting message send task with %d messenger(s), "
                "limit=%s, order=%s."
            ),
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
                    (
                        "Response received for message %s via %s "
                        "with status %s."
                    ),
                    message.id,
                    messenger.__class__.__name__,
                    response.status,
                )
                message_store.store_response(response)

        logger.info(
            (
                "Finished message send task: %d message(s) selected, "
                "%d send attempt(s), %d successful response(s), "
                "%d failed send(s)."
            ),
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
