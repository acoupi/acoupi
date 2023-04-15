"""Process templates for Acoupi.

Acoupi offers a collection of process templates to assist in the creation of
recording, detecting, and data sending processes. While Acoupi includes a
variety of components to construct these processes, users may prefer to use
their own components. By utilizing the provided templates, users can ensure
that their custom processes integrate with Acoupi and adhere to standardized
building practices. The use of templates also allows for effortless
customization of processes.

The templates provided take the form of functions that return a function that
can be used to start a process. Each template takes a set of arguments that
are used to construct the process. The arguments are Acoupi components
of the appropriate type, such as a message store, messenger, model, etc.
Any object that implements the appropriate interface can be used as an
argument. This allows users to use out-of-the-box components or components
that they have created themselves.
"""
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
