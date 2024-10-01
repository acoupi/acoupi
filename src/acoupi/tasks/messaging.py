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
from typing import Callable, List, Optional

from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_send_messages_task(
    message_store: types.MessageStore,
    messengers: Optional[List[types.Messenger]] = None,
    logger: logging.Logger = logger,
) -> Callable[[], None]:
    """Generate a send data task.

    Parameters
    ----------
    message_store : types.MessageStore
        The message store to get and store messages.
    messengers : Optional[List[types.Messenger]], optional
        The messengers to send messages, by default None.
    logger : logging.Logger, optional
        The logger to log messages, by default logger.

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
    if messengers is None:
        messengers = []

    def send_messages_task() -> None:
        """Send Messages."""
        messages = message_store.get_unsent_messages()

        for message in messages:
            logger.info("MESSAGE TASK")
            logger.info(f"MESSAGE CONTENT: {message.content}")

            if message.content is None:
                logger.debug("MESSAGE IS EMPTY")
                continue

            if len(messengers) == 0:
                logger.info("NO MESSENGER DEFINED")
                continue
                # break

            for messenger in messengers:
                response = messenger.send_message(message)
                logger.info(f"Message Sent - Response Status: {response.status}")
                message_store.store_response(response)

    return send_messages_task
