"""Messengers for the acoupi package."""
import datetime
import json
from dataclasses import asdict
from typing import Optional

import paho.mqtt.client as mqtt

from acoupi import types

__all__ = [
    "MQTTMessenger",
    "build_deployment_message",
    "build_recording_message",
    "build_detection_message",
]


def build_deployment_message(deployment: types.Deployment) -> types.Message:
    """Build a deployment message."""
    return types.Message(
        message=json.dumps(asdict(deployment)),
        sent_on=datetime.datetime.now(),
        device_id=deployment.device_id,
    )


def build_recording_message(recording: types.Recording) -> types.Message:
    """Build a recording message."""
    return types.Message(
        message=json.dumps(asdict(recording)),
        sent_on=datetime.datetime.now(),
        device_id="device",  # TODO: get device id from recording
    )


def build_detection_message(detection: types.Detection) -> types.Message:
    """Build a detection message."""
    return types.Message(
        message=json.dumps(asdict(detection)),
        sent_on=datetime.datetime.now(),
        device_id="device",  # TODO: get device id from detection
    )


class MQTTMessenger(types.Messenger):
    """Messenger that sends messages via MQTT."""

    client: mqtt.Client
    """The MQTT client."""

    topic: str
    """The MQTT topic to send messages to."""

    timeout: int
    """Timeout for sending messages."""

    def __init__(
        self,
        client_id: str,
        host: str,
        username: str,
        topic: str,
        password: Optional[str] = None,
        port: int = 1884,
        timeout: int = 5,
    ) -> None:
        """Initialize the MQTT messenger."""
        self.topic = topic
        self.timeout = timeout
        self.client = mqtt.Client(client_id=client_id)
        self.client.username_pw_set(username, password)
        self.client.connect(host, port=port)

    def send_message(self, message: types.Message) -> types.Response:
        """Send a recording message."""
        status = types.ResponseStatus.SUCCESS

        try:
            response = self.client.publish(
                self.topic,
                payload=message.message,
            )
            response.wait_for_publish(timeout=5)

            if not response.rc == mqtt.MQTT_ERR_SUCCESS:
                status = types.ResponseStatus.ERROR

        except ValueError:
            status = types.ResponseStatus.ERROR
        except RuntimeError:
            status = types.ResponseStatus.FAILED

        received_on = datetime.datetime.now()

        return types.Response(
            message=message,
            status=status,
            received_on=received_on,
        )
