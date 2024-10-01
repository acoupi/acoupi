"""Test output cleaners."""

import datetime
from pathlib import Path
from typing import List

import pytest

from acoupi import data
from acoupi.components import output_cleaners


@pytest.fixture
def create_test_model_output():
    """Return a model output."""
    deployment = data.Deployment(
        name="test_deployment",
    )

    recording = data.Recording(
        path=Path("test.wav"),
        duration=1,
        samplerate=256000,
        audio_channels=1,
        deployment=deployment,
        created_on=datetime.datetime.now(),
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


@pytest.fixture
def create_test_detection():
    """Fixture for creating random detections.

    Will create detections with no location and a single tag.
    """

    def factory(
        tag_value: str,
        detection_score: float = 0.5,
        tag_score: float = 1,
        tag_key: str = "species",
    ) -> data.Detection:
        """Return a random detection."""
        return data.Detection(
            detection_score=detection_score,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(
                        value=tag_value,
                        key=tag_key,
                    ),
                    confidence_score=tag_score,
                ),
            ],
        )

    return factory


def test_threshold_detection_filter_removes_detections_with_low_confidence(
    create_test_model_output,
    create_test_detection,
):
    """Test threshold filter removes detections with low confidence."""
    # Arrange
    cleaner = output_cleaners.ThresholdDetectionCleaner(
        detection_threshold=0.5,
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                "species1",
                detection_score=0.1,
                tag_score=0.5,
            ),
            create_test_detection(
                "species2",
                detection_score=0.6,
                tag_score=0.5,
            ),
        ]
    )

    # Act
    cleaned_model_output = cleaner.clean(model_output)

    # Assert
    assert len(cleaned_model_output.detections) == 1
    assert cleaned_model_output.detections[0].tags[0].tag.value == "species2"


def test_threshold_detection_keeps_detections_even_with_low_confidence_tags(
    create_test_model_output,
    create_test_detection,
):
    """Test threshold filter keeps detections even with low confidence tags."""
    cleaner = output_cleaners.ThresholdDetectionCleaner(
        detection_threshold=0.5,
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                "species1",
                detection_score=0.7,
                tag_score=0.1,
            ),
            create_test_detection(
                "species2",
                detection_score=0.6,
                tag_score=0.5,
            ),
        ]
    )

    # Act
    cleaned_model_output = cleaner.clean(model_output)

    # Assert
    assert len(cleaned_model_output.detections) == 2


def test_threshold_removes_detections_with_default_tag_score(
    create_test_model_output,
    create_test_detection,
):
    """Test threshold filter removes detections with default tag score."""
    # Arrange
    cleaner = output_cleaners.ThresholdDetectionCleaner(
        detection_threshold=0.5,
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                "species1",
                detection_score=0.7,
                tag_score=0.5,
            ),
            create_test_detection(
                "species2",
                detection_score=0.3,
            ),
        ]
    )

    # Act
    cleaned_model_output = cleaner.clean(model_output)

    # Assert

    assert len(cleaned_model_output.detections) == 1
    assert cleaned_model_output.detections[0].tags[0].tag.value == "species1"


def test_threshold_removes_low_score_tags(
    create_test_model_output,
    create_test_detection,
):
    """Test filter keeps tags even if with low score score."""
    # Arrange
    cleaner = output_cleaners.ThresholdDetectionCleaner(
        detection_threshold=0.5,
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                "species1",
                detection_score=0.7,
                tag_score=0.1,
            ),
        ]
    )

    # Act
    cleaned_model_output = cleaner.clean(model_output)

    # Assert
    assert len(cleaned_model_output.detections) == 1
    assert len(cleaned_model_output.detections[0].tags) == 0
