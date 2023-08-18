"""Test suite for acoupi messengers."""
import datetime
from pathlib import Path
from unittest import mock

import pytest_httpserver

from acoupi import data
from acoupi.components import messengers


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
            data="Hello, world!",
            params={},
            headers={"Content-Type": "application/json"},
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
            data="Hello, world!",
            params={"key": "value"},
            headers={"Content-Type": "application/json"},
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
            data="Hello, world!",
            params={},
            headers={"Content-Type": "application/json", "X-Test": "value"},
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
            model_name="test_model",
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
                    probability=0.5,
                    tags=[
                        data.PredictedTag(
                            tag=data.Tag(
                                key="test_tag",
                                value="test_value",
                            ),
                            probability=0.2,
                        ),
                        data.PredictedTag(
                            tag=data.Tag(
                                key="event",
                                value="echolocation",
                            ),
                            probability=0.8,
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
            data=model_output.model_dump(mode="json"),
            params={},
            headers={"Content-Type": "application/json"},
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
