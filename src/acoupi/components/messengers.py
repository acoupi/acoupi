"""Messengers for the acoupi package."""
import datetime
from typing import Optional

import paho.mqtt.client as mqtt

from acoupi import data
from acoupi.components import types

__all__ = [
    "MQTTMessenger",
]


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

    def send_message(self, message: data.Message) -> data.Response:
        """Send a recording message."""
        status = data.ResponseStatus.SUCCESS

        try:
            response = self.client.publish(
                self.topic,
                payload=message.content,
            )
            response.wait_for_publish(timeout=5)

            if not response.rc == mqtt.MQTT_ERR_SUCCESS:
                status = data.ResponseStatus.ERROR

        except ValueError:
            status = data.ResponseStatus.ERROR
        except RuntimeError:
            status = data.ResponseStatus.FAILED

        received_on = datetime.datetime.now()

        return data.Response(
            message=message,
            status=status,
            received_on=received_on,
        )
