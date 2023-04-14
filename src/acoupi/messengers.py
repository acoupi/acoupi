"""Messengers for the acoupi package."""
from typing import Optional
import datetime

import paho.mqtt.client as mqtt

from acoupi import types


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
        port: int = 1883,
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
