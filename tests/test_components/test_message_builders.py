"""Test suite for message builder components."""

import datetime
from pathlib import Path

import pytest_httpserver
from werkzeug import Request, Response

from acoupi import components, data

TEST_MODEL_OUTPUT = data.ModelOutput(
    name_model="test_model",
    recording=data.Recording(
        path=Path("test_path.wav"),
        deployment=data.Deployment(
            name="test_deployment",
        ),
        duration=1,
        samplerate=192000,
        datetime=datetime.datetime(2020, 1, 1, 0, 0, 0),
    ),
    tags=[
        data.PredictedTag(
            tag=data.Tag(key="species", value="Myotis myotis"),
            confidence_score=0.9,
        ),
        data.PredictedTag(
            tag=data.Tag(key="species", value="Eptesicus serotinus"),
            confidence_score=0.7,
        ),
        data.PredictedTag(
            tag=data.Tag(key="antropophony", value="Human voice"),
            confidence_score=0.4,
        ),
    ],
    detections=[
        data.Detection(
            location=data.BoundingBox(
                coordinates=(0.1, 15_000, 0.2, 30_000),
            ),
            detection_probability=0.9,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(key="species", value="Myotis myotis"),
                    confidence_score=0.6,
                ),
                data.PredictedTag(
                    tag=data.Tag(key="event", value="Echolocation"),
                    confidence_score=0.8,
                ),
            ],
        ),
        data.Detection(
            location=data.BoundingBox(
                coordinates=(0.5, 19_000, 0.7, 38_000),
            ),
            detection_probability=0.6,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(key="species", value="Myotis myotis"),
                    confidence_score=0.5,
                ),
                data.PredictedTag(
                    tag=data.Tag(key="event", value="Feeding buzz"),
                    confidence_score=0.4,
                ),
            ],
        ),
        data.Detection(
            location=data.BoundingBox(
                coordinates=(0.9, 24_000, 0.95, 41_000),
            ),
            detection_probability=0.4,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(key="species", value="Eptesicus serotinus"),
                    confidence_score=0.7,
                ),
            ],
        ),
    ],
)


def test_full_model_output_message_builder_returns_a_message():
    """Test that the FullModelOutputMessageBuilder returns a message."""
    builder = components.FullModelOutputMessageBuilder()
    message = builder.build_message(TEST_MODEL_OUTPUT)
    assert isinstance(message, data.Message)


def test_full_model_output_message_builder_returns_the_correct_message():
    """Test that FullModelOutputMessageBuilder returns the correct message."""
    builder = components.FullModelOutputMessageBuilder()
    message = builder.build_message(TEST_MODEL_OUTPUT)
    assert message.content == TEST_MODEL_OUTPUT.model_dump_json()


def test_full_model_output_message_can_be_sent_with_http_messenger(
    httpserver: pytest_httpserver.HTTPServer,
):
    """Test the HTTPMessenger fails with a bad request."""
    # Arrange

    def handler(
        request: Request,
    ) -> Response:
        """Handle the request."""
        assert request.method == "POST"
        assert request.headers["Content-Type"] == "application/json"
        request_data = request.data.decode("utf-8")
        request_data = data.ModelOutput.model_validate_json(request_data)
        assert request_data == TEST_MODEL_OUTPUT
        return Response("OK", status=200)

    httpserver.expect_request("/endpoint").respond_with_handler(
        handler,
    )
    messenger = components.HTTPMessenger(
        base_url=httpserver.url_for("/endpoint"),
    )

    message = components.FullModelOutputMessageBuilder().build_message(
        TEST_MODEL_OUTPUT,
    )

    # Act
    response = messenger.send_message(message)

    # Assert
    assert response.status == data.ResponseStatus.SUCCESS
    assert response.content == "OK"
