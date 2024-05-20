"""Test suite for acoupi messengers."""

import datetime
from pathlib import Path
from unittest import mock

import pytest
import pytest_httpserver
from paho.mqtt.enums import MQTTErrorCode

from acoupi import data
from acoupi.components import messengers
from acoupi.system.exceptions import HealthCheckError


def test_http_messenger():
    """Test the HTTPMessenger."""
    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"

        messenger = messengers.HTTPMessenger(
            base_url="http://localhost:5000",
            timeout=5,
        )

        message = data.Message(content='"Hello, world!"')

        response = messenger.send_message(message)

        assert response.status == data.ResponseStatus.SUCCESS
        assert response.content == "OK"

        mock_post.assert_called_once_with(
            "http://localhost:5000",
            json="Hello, world!",
            params={},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=5,
        )


def test_http_messenger_with_params():
    """Test the HTTPMessenger with parameters."""
    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"

        messenger = messengers.HTTPMessenger(
            base_url="http://localhost:5000",
            base_params={"key": "value"},
            timeout=5,
        )

        message = data.Message(content='"Hello, world!"')

        response = messenger.send_message(message)

        assert response.status == data.ResponseStatus.SUCCESS
        assert response.content == "OK"

        mock_post.assert_called_once_with(
            "http://localhost:5000",
            json="Hello, world!",
            params={"key": "value"},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=5,
        )


def test_http_messeger_with_custom_headers():
    """Test the HTTPMessenger with custom headers."""
    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"

        messenger = messengers.HTTPMessenger(
            base_url="http://localhost:5000",
            headers={"X-Test": "value"},
            timeout=5,
        )

        message = data.Message(content='"Hello, world!"')

        response = messenger.send_message(message)

        assert response.status == data.ResponseStatus.SUCCESS
        assert response.content == "OK"

        mock_post.assert_called_once_with(
            "http://localhost:5000",
            json="Hello, world!",
            params={},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Test": "value",
            },
            timeout=5,
        )


def test_http_messenger_with_complex_message():
    """Test the HTTPMessenger with a complex message."""
    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"

        messenger = messengers.HTTPMessenger(
            base_url="http://localhost:5000",
            timeout=5,
        )

        model_output = data.ModelOutput(
            name_model="test_model",
            recording=data.Recording(
                path=Path("test_recording.wav"),
                duration=1,
                samplerate=16000,
                datetime=datetime.datetime.now(),
                deployment=data.Deployment(
                    name="test_deployment",
                ),
            ),
            detections=[
                data.Detection(
                    location=data.BoundingBox(
                        coordinates=(0, 0, 1, 1),
                    ),
                    detection_probability=0.5,
                    tags=[
                        data.PredictedTag(
                            tag=data.Tag(
                                key="test_tag",
                                value="test_value",
                            ),
                            classification_probability=0.2,
                        ),
                        data.PredictedTag(
                            tag=data.Tag(
                                key="event",
                                value="echolocation",
                            ),
                            classification_probability=0.8,
                        ),
                    ],
                ),
            ],
        )

        message = data.Message(content=model_output.model_dump_json())

        response = messenger.send_message(message)

        assert response.status == data.ResponseStatus.SUCCESS
        assert response.content == "OK"

        mock_post.assert_called_once_with(
            "http://localhost:5000",
            json=model_output.model_dump(mode="json"),
            params={},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=5,
        )


def test_http_messenger_is_sending_a_message(
    httpserver: pytest_httpserver.HTTPServer,
):
    """Test the HTTPMessenger is sending a message."""
    # Arrange
    httpserver.expect_request("/endpoint").respond_with_data("OK")
    messenger = messengers.HTTPMessenger(
        base_url=httpserver.url_for("/endpoint"),
        timeout=5,
    )
    message = data.Message(content='"Hello, world!"')

    # Act
    response = messenger.send_message(message)

    # Assert
    assert response.status == data.ResponseStatus.SUCCESS
    assert response.content == "OK"


def test_http_messenger_fails_with_bad_request(
    httpserver: pytest_httpserver.HTTPServer,
):
    """Test the HTTPMessenger fails with a bad request."""
    # Arrange
    httpserver.expect_request("/endpoint").respond_with_data(
        "BAD REQUEST",
        status=400,
    )
    messenger = messengers.HTTPMessenger(
        base_url=httpserver.url_for("/endpoint"),
        timeout=5,
    )
    message = data.Message(content='"Hello, world!"')

    # Act
    response = messenger.send_message(message)

    # Assert
    assert response.status == data.ResponseStatus.ERROR
    assert response.content == "BAD REQUEST"


def test_http_check_is_successful(httpserver: pytest_httpserver.HTTPServer):
    """Test the HTTPMessenger check connection is successful."""
    # Arrange
    httpserver.expect_request("/", method="OPTIONS").respond_with_data("OK")
    messenger = messengers.HTTPMessenger(
        base_url=httpserver.url_for("/"),
        timeout=5,
    )

    # Act
    messenger.check()


def test_http_check_fails_is_cannot_connect():
    """Test the HTTPMessenger check connection fails if cannot connect."""
    # Arrange
    messenger = messengers.HTTPMessenger(
        base_url="http://localhost:5000",
        timeout=5,
    )

    # Act
    with pytest.raises(HealthCheckError):
        messenger.check()


def test_http_check_fails_is_not_allowed(
    httpserver: pytest_httpserver.HTTPServer,
):
    """Test the HTTPMessenger check connection fails if not allowed."""
    # Arrange
    httpserver.expect_request("/", method="OPTIONS").respond_with_data(
        "NOT ALLOWED",
        status=405,
    )
    messenger = messengers.HTTPMessenger(
        base_url=httpserver.url_for("/"),
        timeout=5,
    )

    # Act
    with pytest.raises(HealthCheckError, match="405"):
        messenger.check()


def test_http_check_fails_if_post_not_allowed(
    httpserver: pytest_httpserver.HTTPServer,
):
    """Test the HTTPMessenger check connection fails if POST not allowed."""
    # Arrange
    httpserver.expect_request("/", method="OPTIONS").respond_with_data(
        "OK", headers={"Allow": "GET"}
    )
    messenger = messengers.HTTPMessenger(
        base_url=httpserver.url_for("/"),
        timeout=5,
    )

    # Act
    with pytest.raises(HealthCheckError, match="POST"):
        messenger.check()


def test_mqtt_messenger_can_send_simple_message():
    """Test the MQTTMessenger can send a simple message."""
    # Arrange
    mock_response = mock.MagicMock()
    mock_response.rc = 0
    config = {
        "is_connected.return_value": True,
        "publish.return_value": mock_response,
    }

    with mock.patch(
        "paho.mqtt.client.Client",
        spec=True,
        **config,
    ) as mock_client:
        messenger = messengers.MQTTMessenger(
            host="localhost",
            port=1883,
            username="test",
            topic="acoupi",
            clientid="test",
        )
        message = data.Message(content='"Hello, world!"')

        # Act
        response = messenger.send_message(message)

        # Assert
        assert response.status == data.ResponseStatus.SUCCESS
        assert response.content == "MQTT_ERR_SUCCESS"

        mock_client.return_value.publish.assert_called_once_with(
            topic="acoupi",
            payload='"Hello, world!"',
        )


def test_mqtt_check_is_succesful_when_connected():
    """Test the MQTTMessenger check connection is successful when connected."""
    # Arrange
    config = {
        "is_connected.return_value": True,
    }

    with mock.patch(
        "paho.mqtt.client.Client",
        spec=True,
        **config,
    ):
        messenger = messengers.MQTTMessenger(
            host="localhost",
            port=1883,
            username="test",
            topic="acoupi",
            clientid="test",
        )

        # Act
        messenger.check()


def test_mqtt_check_is_succesful_when_can_reconnect():
    """Test the MQTTMessenger check connection is successful when can reconnect."""
    # Arrange
    config = {
        "is_connected.return_value": False,
        "host": "localhost",
        "reconnect.return_value": 0,
    }

    with mock.patch(
        "paho.mqtt.client.Client",
        spec=True,
        **config,
    ):
        messenger = messengers.MQTTMessenger(
            host="localhost",
            port=1883,
            username="test",
            topic="acoupi",
            clientid="test",
        )

        # Act
        messenger.check()


def test_mqtt_check_is_successful_when_can_connect():
    """Test the MQTTMessenger check connection is successful when can connect."""
    # Arrange
    config = {
        "is_connected.return_value": False,
        "host": None,
        "connect.return_value": 0,
    }

    with mock.patch(
        "paho.mqtt.client.Client",
        spec=True,
        **config,
    ):
        messenger = messengers.MQTTMessenger(
            host="localhost",
            port=1883,
            username="test",
            topic="acoupi",
            clientid="test",
        )

        # Act
        messenger.check()


@pytest.mark.parametrize(
    "error_code",
    range(1, 17),
)
def test_mqtt_check_fails_with_mqtt_error_on_connection(error_code: int):
    """Test the MQTTMessenger check connection fails with MQTT error."""
    # Arrange
    config = {
        "is_connected.return_value": False,
        "host": None,
        "connect.return_value": error_code,
    }

    with mock.patch(
        "paho.mqtt.client.Client",
        spec=True,
        **config,
    ):
        messenger = messengers.MQTTMessenger(
            host="localhost",
            port=1883,
            username="test",
            topic="acoupi",
            clientid="test",
        )

        # Act
        with pytest.raises(
            HealthCheckError,
            match=MQTTErrorCode(error_code).name,
        ):
            messenger.check()


@pytest.mark.parametrize(
    "error_code",
    range(1, 17),
)
def test_mqtt_check_fails_with_mqtt_error_on_reconnection(error_code: int):
    """Test the MQTTMessenger check connection fails with MQTT error."""
    # Arrange
    config = {
        "is_connected.return_value": False,
        "host": "localhost",
        "reconnect.return_value": error_code,
    }

    with mock.patch(
        "paho.mqtt.client.Client",
        spec=True,
        **config,
    ):
        messenger = messengers.MQTTMessenger(
            host="localhost",
            port=1883,
            username="test",
            topic="acoupi",
            clientid="test",
        )

        # Act
        with pytest.raises(
            HealthCheckError,
            match=MQTTErrorCode(error_code).name,
        ):
            messenger.check()
