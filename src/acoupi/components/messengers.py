"""Messengers for the acoupi package."""

import datetime
import json
from typing import Optional
import logging
from acoupi.system.exceptions import HealthCheckError
from celery.utils.log import get_task_logger

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
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

    logger: logging.Logger

    def __init__(
        self,
        host: str,
        username: str,
        topic: str,
        clientid: str,
        port: int = 1884,
        password: Optional[str] = None,
        timeout: int = 5,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the MQTT messenger."""
        self.topic = topic
        self.timeout = timeout
        self.host = host
        self.port = port
        self.client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=clientid,
        )
        self.client.username_pw_set(username, password)

        if logger is None:
            logger = get_task_logger(__name__)

        self.logger = logger

    def check_connection(self) -> MQTTErrorCode:
        """Check the connection status of the MQTT client."""
        if self.client.is_connected():
            return MQTTErrorCode.MQTT_ERR_SUCCESS

        # NOTE: According to the docs, the host attribute is only set after
        # the connect method is called. If the host attribute is set, then
        # its better to use the reconnect method.
        if self.client.host == self.host:
            return self.client.reconnect()

        return self.client.connect(self.host, port=self.port)

    def send_message(self, message: data.Message) -> data.Response:
        """Send a recording message."""
        mqtt_status = self.check_connection()

        if mqtt_status != MQTTErrorCode.MQTT_ERR_SUCCESS:
            self.logger.warning(f"MQTT connection error: {mqtt_status}")
            return data.Response(
                message=message,
                status=data.ResponseStatus.ERROR,
                received_on=datetime.datetime.now(),
            )

        response = self.client.publish(
            topic=self.topic,
            payload=message.content,
        )

        status = data.ResponseStatus.SUCCESS
        try:
            response.wait_for_publish(timeout=5)
        except ValueError as e:
            status = data.ResponseStatus.ERROR
            logging.debug(f"Message not sent: {message.content}. Error: {e}")
        except RuntimeError as e:
            status = data.ResponseStatus.FAILED
            logging.debug(f"Message not sent: {message.content}. Error: {e}")

        if response.rc != MQTTErrorCode.MQTT_ERR_SUCCESS:
            logging.debug(
                f"Message not sent: {message.content}. Error: {response.rc}"
            )
            status = data.ResponseStatus.ERROR

        received_on = datetime.datetime.now()
        logging.debug(f"Message sent: {message.content}")

        return data.Response(
            message=message,
            status=status,
            content=MQTTErrorCode(response.rc).name,
            received_on=received_on,
        )

    def check(self) -> None:
        """Check the connection status of the MQTT client."""
        mqtt_status = self.check_connection()

        if mqtt_status != MQTTErrorCode.MQTT_ERR_SUCCESS:
            error_name = MQTTErrorCode(mqtt_status).name
            raise HealthCheckError(
                f"Health check failed: MQTT Connection Error ({error_name}).\n"
                "Possible causes:\n"
                "  * Broker unavailable: Ensure the MQTT broker is running "
                "and accessible.\n"
                "  * Authentication failed: Verify your MQTT credentials "
                "(username/password) are correct.\n"
                "  * Network issues: Check your network connection and any "
                "firewall settings.\n"
                "  * Misconfiguration: Review your MQTT configuration "
                "parameters for accuracy."
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
        content_json = json.loads(message_content)

        try:
            if self.content_type == "application/json":
                response = requests.post(
                    self.base_url,
                    json=content_json,
                    params=self.base_params,
                    headers=self.headers,
                    timeout=self.timeout,
                )

            else:
                response = requests.post(
                    self.base_url,
                    data=content_json,
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

    def check(self) -> None:
        """Check the connection status of the HTTP client.

        Raises
        ------
        HealthCheckError
            If the connection is not successful. This could be due to a
            connection error or if the POST method is not allowed.
        """
        try:
            response = requests.options(self.base_url)
        except requests.exceptions.ConnectionError as err:
            raise HealthCheckError(
                f"Health check failed: Unable to connect to {self.base_url}.\n"
                "Possible causes:\n"
                f"  * Incorrect URL: Double-check that '{self.base_url}' is "
                "the correct address.\n"
                "  * Network issues: Verify your internet connection or any "
                "firewall settings.\n"
                "  * Service down: The server at {self.base_url} may be "
                "temporarily unavailable."
            ) from err

        if not response.ok:
            status_code = response.status_code
            error_type = "Client" if 400 <= status_code < 500 else "Server"
            raise HealthCheckError(
                f"Health check failed for {self.base_url}: {error_type} "
                f"Error ({status_code}).\n"
                "Could connect to the server but received an error response.\n"
                "Possible causes:\n"
                "  * 4xx Client Error: Missing authentication credentials, or "
                "authorization issues.\n"
                f"  * 5xx Server Error:  The service at {self.base_url} is "
                "temporarily unavailable or experiencing issues."
            )

        if (
            "Allow" in response.headers
            and "POST" not in response.headers["Allow"]
        ):
            raise HealthCheckError(
                f"Could connect to {self.base_url} but POST method is "
                "not allowed. Check the server configuration."
            )
