"""Test acoupi components saving filters."""

import datetime
from pathlib import Path
from typing import List
import tempfile
import pytz
from astral import LocationInfo
from astral.sun import sun

import pytest

from acoupi import data
from acoupi.components import saving_filters


@pytest.fixture
def create_test_recording():
    """Fixture for creating random recording.

    Will create a recording with a path, duration, samplerate, deployment and datetime.
    """
    deployment = data.Deployment(
        name="test_deployment",
    )

    def factory(
        recording_time: datetime.datetime,
        recording_path: Path = Path("test.wav"),
        duration: float = 1,
        samplerate: int = 256000,
        audio_channels: int = 1,
    ) -> data.Recording:
        """Return a recording."""
        return data.Recording(
            path=recording_path,
            duration=duration,
            samplerate=samplerate,
            audio_channels=audio_channels,
            deployment=deployment,
            created_on=recording_time,
        )

    return factory


@pytest.fixture
def create_test_detection():
    """Fixture for creating random detections.

    Will create detections with no location and a single tag.
    """

    def factory(
        tag_value: str,
        tag_key: str = "species",
        confidence_score: float = 0.4,
        detection_score: float = 0.8,
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
                    confidence_score=confidence_score,
                ),
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


""" TESTS - RECORDING TIME INTERVAL - SAVING FILTERS"""


def test_save_recording_ifin_interval(
    create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    time_interval = data.TimeInterval(
        start=datetime.time(22, 0, 0),
        end=datetime.time(4, 0, 0),
    )
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 23, 0, 0),
    )

    saving_filter = saving_filters.SaveIfInInterval(
        interval=time_interval, timezone=datetime.timezone.utc
    )
    # Act
    result = saving_filter.should_save_recording(recording)

    # Check
    assert result is True


def test_delete_recording_ifnotin_interval(
    create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    time_interval = data.TimeInterval(
        start=datetime.time(22, 0, 0),
        end=datetime.time(4, 0, 0),
    )
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 12, 0, 0),
    )

    saving_filter = saving_filters.SaveIfInInterval(
        interval=time_interval, timezone=datetime.timezone.utc
    )
    # Act
    result = saving_filter.should_save_recording(recording)

    # Check
    assert result is False


""" TESTS - DAWN DUSK TIME INTERVAL - SAVING FILTERS """


def test_before_dawndusk_time_interval(
    create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    interval_duration: float = 20  # in minutes
    timezone = pytz.timezone("Europe/London")

    saving_filter = saving_filters.Before_DawnDuskTimeInterval(
        duration=interval_duration, timezone=timezone
    )

    # Fetch sun information
    test_date = datetime.datetime(2024, 8, 1, tzinfo=timezone)
    sun_info = sun(
        LocationInfo(str(timezone)).observer, date=test_date, tzinfo=timezone
    )
    dawntime = sun_info["dawn"]
    dusktime = sun_info["dusk"]

    # Case 1: Recording within the interval before dusk
    recording_inside_duskinterval = create_test_recording(
        dusktime - datetime.timedelta(minutes=10)
    )
    assert (
        saving_filter.should_save_recording(recording_inside_duskinterval)
        is True
    )

    # Case 2: Recording outside the interval before dusk
    recording_outside_duskinterval = create_test_recording(
        dusktime - datetime.timedelta(minutes=40)
    )
    assert (
        saving_filter.should_save_recording(recording_outside_duskinterval)
        is False
    )

    # Case 3: Recording within the interval before dawn
    recording_inside_dawninterval = create_test_recording(
        dawntime - datetime.timedelta(minutes=10)
    )
    assert (
        saving_filter.should_save_recording(recording_inside_dawninterval)
        is True
    )

    # Case 4: Recording outside the interval before dawn
    recording_outside_dawninterval = create_test_recording(
        dawntime - datetime.timedelta(minutes=40)
    )
    assert (
        saving_filter.should_save_recording(recording_outside_dawninterval)
        is False
    )


def test_after_dawndusk_time_interval(
    create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    interval_duration: float = 20  # in minutes
    timezone = pytz.timezone("Europe/London")

    saving_filter = saving_filters.After_DawnDuskTimeInterval(
        duration=interval_duration, timezone=timezone
    )

    # Fetch sun information
    test_date = datetime.datetime(2024, 8, 1, tzinfo=timezone)
    sun_info = sun(
        LocationInfo(str(timezone)).observer, date=test_date, tzinfo=timezone
    )
    dawntime = sun_info["dawn"]
    dusktime = sun_info["dusk"]

    # Case 1: Recording within the interval before dusk
    recording_inside_duskinterval = create_test_recording(
        dusktime + datetime.timedelta(minutes=10)
    )
    assert (
        saving_filter.should_save_recording(recording_inside_duskinterval)
        is True
    )

    # Case 2: Recording outside the interval before dusk
    recording_outside_duskinterval = create_test_recording(
        dusktime + datetime.timedelta(minutes=40)
    )
    assert (
        saving_filter.should_save_recording(recording_outside_duskinterval)
        is False
    )

    # Case 3: Recording within the interval before dawn
    recording_inside_dawninterval = create_test_recording(
        dawntime + datetime.timedelta(minutes=10)
    )
    assert (
        saving_filter.should_save_recording(recording_inside_dawninterval)
        is True
    )

    # Case 4: Recording outside the interval before dawn
    recording_outside_dawninterval = create_test_recording(
        dawntime + datetime.timedelta(minutes=40)
    )
    assert (
        saving_filter.should_save_recording(recording_outside_dawninterval)
        is False
    )


""" TESTS - THRESHOLD DETECTIONS - SAVING FILTERS """


def test_delete_recording_without_detections(
    create_test_recording,
    create_test_model_output,
) -> None:
    """Test if the recording is deleted if it has no detections."""
    # Setup
    saving_threshold = 0.6
    # create tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        temp_path = tmpfile.name

    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
        recording_path=Path(temp_path),
    )

    model_output = create_test_model_output(detections=[])

    saving_filter = saving_filters.SavingThreshold(
        saving_threshold=saving_threshold
    )
    # Act
    result = saving_filter.should_save_recording(
        recording, model_outputs=[model_output]
    )

    # Check
    assert not result
    assert result is False


def test_save_recording_ifboth_detclassprob_above_savingthreshold(
    create_test_detection,
    create_test_recording,
    create_test_model_output,
) -> None:
    """Test if the recording is saved if both det. and class. probabilities are above the saving threshold."""
    # Setup
    saving_threshold = 0.6
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                confidence_score=0.7,
                detection_score=0.8,
            ),
            create_test_detection(
                tag_value="species_2",
                confidence_score=0.8,
                detection_score=0.9,
            ),
        ]
    )

    saving_filter = saving_filters.SavingThreshold(
        saving_threshold=saving_threshold
    )
    # Act
    result = saving_filter.should_save_recording(
        recording, model_outputs=[model_output]
    )

    # Check
    assert result is True


def test_save_recording_if_onlydetprob_above_savingthreshold(
    create_test_detection,
    create_test_recording,
    create_test_model_output,
) -> None:
    """Test if the recording is saved if only detection probabilities are above the saving threshold."""
    # Setup
    saving_threshold = 0.6
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                confidence_score=0.4,
                detection_score=0.8,
            ),
            create_test_detection(
                tag_value="species_2",
                confidence_score=0.3,
                detection_score=0.7,
            ),
        ]
    )

    saving_filter = saving_filters.SavingThreshold(
        saving_threshold=saving_threshold
    )
    # Act
    result = saving_filter.should_save_recording(
        recording, model_outputs=[model_output]
    )

    # Check
    assert result is True


def test_delete_recording_if_detclassprob_below_savingthreshold(
    create_test_model_output,
    create_test_recording,
    create_test_detection,
) -> None:
    """Test if the recording is deleted if none of the probabilities are above the saving threshold."""
    # Setup
    saving_threshold = 0.6

    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        temp_path = tmpfile.name

    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
        recording_path=Path(temp_path),
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                confidence_score=0.4,
                detection_score=0.5,
            ),
            create_test_detection(
                tag_value="species_2",
                confidence_score=0.3,
                detection_score=0.4,
            ),
        ]
    )

    saving_filter = saving_filters.SavingThreshold(
        saving_threshold=saving_threshold
    )
    # Act
    result = saving_filter.should_save_recording(
        recording, model_outputs=[model_output]
    )

    # Check
    assert not result
    assert result is False


""" TESTS - TAG VALUES - SAVING FILTERS """


def test_save_recording_with_focus_tagvalues(
    create_test_recording,
    create_test_model_output,
    create_test_detection,
) -> None:
    """Test if the recording is saved if it contains a focus tag value (e.g., name of a species)."""
    # Setup
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
    )
    focus_species = ["species_1", "species_2"]
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                confidence_score=0.4,
                detection_score=0.8,
            ),
            create_test_detection(
                tag_value="species_2",
                confidence_score=0.3,
                detection_score=0.7,
            ),
        ]
    )

    saving_filter = saving_filters.DetectionTagValue(values=focus_species)
    # Act
    result = saving_filter.should_save_recording(
        recording, model_outputs=[model_output]
    )

    # Check
    assert result is True


def test_delete_recording_ifnot_focus_tagvalues(
    create_test_recording,
    create_test_detection,
    create_test_model_output,
) -> None:
    """Test if the recording is saved if it contains the focus species."""
    # Setup
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
    )
    focus_species = ["species_1", "species_2"]
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_3",
                confidence_score=0.4,
                detection_score=0.8,
            ),
            create_test_detection(
                tag_value="species_4",
                confidence_score=0.3,
                detection_score=0.7,
            ),
        ]
    )

    saving_filter = saving_filters.DetectionTagValue(values=focus_species)
    # Act
    result = saving_filter.should_save_recording(
        recording, model_outputs=[model_output]
    )

    # Check
    assert result is False


""" TESTS - FOCUS TAGS - SAVING FILTERS """
