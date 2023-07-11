"""Messengers for the acoupi package."""
import datetime
import json
from typing import Optional

import paho.mqtt.client as mqtt
import requests

from acoupi import data
from acoupi.components import types

__all__ = [
    "MQTTMessenger",
    "HTTPMessenger",
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
        host: str,
        username: str,
        topic: str,
        clientid: str,
        port: int = 1884,
        password: Optional[str] = None,
        timeout: int = 5,
    ) -> None:
        """Initialize the MQTT messenger."""
        self.topic = topic
        self.timeout = timeout
        self.client = mqtt.Client(client_id=clientid)
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


class HTTPMessenger(types.Messenger):
    """Messenger that sends messages via HTTP POST requests."""

    base_url: str
    """The base URL to send messages to."""

    timeout: int
    """Timeout for sending messages in seconds."""

    base_params: dict
    # base_params: str
    """Base parameters to send with each request."""

    headers: dict
    """Headers to send with each request."""

    def __init__(
        self,
        base_url: str,
        base_params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: int = 5,
        content_type: str = "application/json",
    ) -> None:
        """Initialize the HTTP messenger.

        Parameters
        ----------
        base_url : str
            The URL to send messages to. This should include the protocol
            (e.g. http:// or https://) and the hostname (e.g. localhost)
            and the path (e.g. /api/endpoint).
        base_params : Optional[dict], optional
            Base parameters to send with each request, by default None.
        headers : Optional[dict], optional
            Headers to send with each request, by default None.
        timeout : int, optional
            Seconds to wait for a response before timing out, by default 5.
        content_type : str, optional
            The content type to send with each request, by default
            "application/json".

        """
        self.base_url = base_url
        self.timeout = timeout
        self.base_params = base_params or {}
        self.headers = headers or {}

        # Set the content type if not already set
        if self.headers.get("Content-Type") is None:
            self.headers["Content-Type"] = content_type

        # Set accepted content type if not already set
        if self.headers.get("Accept") is None:
            self.headers["Accept"] = content_type

        self.content_type = self.headers["Content-Type"]

    def send_message(self, message: data.Message) -> data.Response:
        """Send a recording message through a HTTP POST request."""
        status = data.ResponseStatus.SUCCESS
        response_content = None

        message_content = message.content
        post_json = {'data:' : message_content}
        print(" --- HTTP MESSAGE CONTENT --- ")
        print(message_content)

        try:
            if self.content_type == "application/json":
                response = requests.post(
                    self.base_url,
                    json=json.loads(message_content),
                    params=self.base_params,
                    headers=self.headers,
                    timeout=self.timeout,
                )

            else:
                response = requests.post(
                    self.base_url,
                    data=message_content,
                    params=self.base_params,
                    headers=self.headers,
                    timeout=self.timeout,
                )

            response_content = response.text

            if not response.ok:
                status = data.ResponseStatus.ERROR

        except ValueError:
            status = data.ResponseStatus.ERROR
        except RuntimeError:
            status = data.ResponseStatus.FAILED

        received_on = datetime.datetime.now()

        return data.Response(
            content=response_content,
            message=message,
            status=status,
            received_on=received_on,
        )
