import logging
from typing import Callable

from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_send_data_task(
    message_store: types.MessageStore,
    messenger: types.Messenger,
) -> Callable[[], None]:
    """Build a process to send data to a remote server.

    Use this function to build a process that will send data to a remote server
    using your preferred messenger and message store. This function will return
    a function that can be used to start the process.

    The built process will send unsynced deployments, recordings, and detections
    to the remote server. The process will then store the response from the
    remote server, so that the data can be marked as synced.

    Args:
        message_store: The message store to use. The message store
            is used to get unsynced data and store any messages that are sent.
        messenger: The messenger to use.

    Returns:
        A function that can be used to start the process.
    """

    def send_data_task() -> None:
        """Process to sync data."""
        for message in message_store.get_unsent_messages():
            response = messenger.send_message(message)
            message_store.store_response(response)

    return send_data_task