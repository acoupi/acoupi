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


def generate_send_data_task(
    message_store: types.MessageStore,
    messengers: Optional[List[types.Messenger]] = None,
    logger: logging.Logger = logger,
) -> Callable[[], None]:
    """Generate a send data task."""
    if messengers is None:
        messengers = []

    def send_data_task() -> None:
        """Send Messages.

        Notes
        -----
        The send data process calls the following methods:

        message_store.get_unsent_messages() -> List[data.Message]
            Get the unsent messages from the message store.
            See acoupi.components.message_stores.sqlite.store for implementation of types.MessageStore.
        messenger.send_message(message) -> data.Response
            Send the messages to a remote server.
            See acoupi.components.messengers for implementation of types.Messenger.
        message_store.store_response(response) -> None
            Store the response from the remote server in the message store.
            See acoupi.components.message_stores.sqlite.store for implementation of types.MessageStore.
        """
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
                logger.info(
                    f"Message Sent - Response Status: {response.status}"
                )
                message_store.store_response(response)

    return send_data_task
