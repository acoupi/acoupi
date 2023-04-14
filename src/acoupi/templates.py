"""Process templates for Acoupi."""

from acoupi import types
from acoupi.messengers import (
    build_deployment_message,
    build_detection_message,
    build_recording_message,
)


def build_sync_data_process(
    message_store: types.MessageStore,
    messenger: types.Messenger,
):
    def sync_data():
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
