"""Test acoupi components saving filters."""

import datetime
from pathlib import Path
from typing import List

import pytest

from acoupi import data
from acoupi.components import message_factories


@pytest.fixture
def create_test_detection():
    """Fixture for creating random detections.

    Will create detections with no location and a single tag.
    """

    def factory(
        detection_probability: float = 0.8,
        tag_key: str = "species",
        tag_value: str = "Myotis myotis",
        confidence_score: float = 0.6,
    ) -> data.Detection:
        """Return a random detection."""
        return data.Detection(
            location=data.BoundingBox(
                coordinates=(0.1, 0.2, 0.3, 0.4),
            ),
            detection_probability=detection_probability,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(
                        key=tag_key,
                        value=tag_value,
                    ),
                    confidence_score=confidence_score,
                )
            ],
        )

    return factory


@pytest.fixture
def create_test_model_output():
    """Fixture for creating random model output."""
    deployment = data.Deployment(
        name="test_deployment",
    )

    recording = data.Recording(
        path=Path("test.wav"),
        duration=1,
        samplerate=256000,
        audio_channels=1,
        deployment=deployment,
        datetime=datetime.datetime.now(),
    )

    def factory(
        detections: List[data.Detection],
    ) -> data.ModelOutput:
        """Return a model output."""
        return data.ModelOutput(
            recording=recording,
            name_model="test_model",
            detections=detections,
        )

    return factory


"""TESTS - DETECTION THRESHOLD - MESSAGE BUILDERS"""


def test_message_builder_detections_below_threshold(
    create_test_detection,
    create_test_model_output,
):
    """Test that detections below the threshold are removed from the message."""
    detection_threshold = 0.6
    message_builder = message_factories.DetectionThresholdMessageBuilder(
        detection_threshold=detection_threshold,
    )

    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                detection_probability=0.5,
                tag_key="species",
                tag_value="species_1",
                confidence_score=0.4,
            ),
        ]
    )

    message = message_builder.build_message(model_output)

    assert message is None


def test_message_builder_detections_with_mixthreshold(
    create_test_detection,
    create_test_model_output,
):
    """Test that detections below the threshold are removed from the message."""
    detection_threshold = 0.6
    message_builder = message_factories.DetectionThresholdMessageBuilder(
        detection_threshold=detection_threshold,
    )

    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                detection_probability=0.5,
                tag_key="species",
                tag_value="species_1",
                confidence_score=0.4,
            ),
            create_test_detection(
                detection_probability=0.7,
                tag_key="species",
                tag_value="species_2",
                confidence_score=0.6,
            ),
        ]
    )
    clean_detections = message_builder.filter_detections(model_output.detections)
    assert len(clean_detections) == 1

    message = message_builder.build_message(model_output)
    assert message is not None
