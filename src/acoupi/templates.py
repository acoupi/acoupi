"""Process templates for Acoupi."""
from typing import Callable

from acoupi import types
from acoupi.messengers import (
    build_deployment_message,
    build_detection_message,
    build_recording_message,
)


def build_send_data_process(
    message_store: types.MessageStore,
    messenger: types.Messenger,
) -> Callable[[], None]:
    """Build a process to send data to a remote server.

    Use this function to build a process that will send data to a remote server
    using your preferred messenger and message store. This function will return
    a function that can be used to start the process.

    Args:
        message_store: The message store to use. The message store
            is used to get unsynced data and store any messages that are sent.
        messenger: The messenger to use.

    Returns:
        A function that can be used to start the process.
    """

    def send_data_process() -> None:
        """Process to sync data."""
        # Sync deployments
        for deployment in message_store.get_unsynced_deployments():
            message = build_deployment_message(deployment)
            response = messenger.send_message(message)
            message_store.store_deployment_message(deployment, response)

        # Sync recordings
        for recording in message_store.get_unsynced_recordings():
            message = build_recording_message(recording)
            response = messenger.send_message(message)
            message_store.store_recording_message(recording, response)

        # Sync detections
        for detection in message_store.get_unsynced_detections():
            message = build_detection_message(detection)
            response = messenger.send_message(message)
            message_store.store_detection_message(detection, response)

    return send_data_process
