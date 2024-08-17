"""Test acoupi components saving filters."""

import datetime
from pathlib import Path
from typing import List
import pytz
from astral import LocationInfo
from astral.sun import sun

import pytest

from acoupi import data
from acoupi.components import saving_filters


@pytest.fixture
def create_test_timeinterval():
    """Fixture for creating random time interval.
    
    Will create a time interval with a start and end time.
    """

    def factory(
        start_time: datetime.time, 
        end_time: datetime.time,
    ) -> data.TimeInterval:
        """Return a time interval."""
        return data.TimeInterval(
            start=start_time,
            end=end_time,
        )
    return factory

@pytest.fixture
def create_test_dawndusk_timeinterval():
    """Fixture for creating random dawn dusk time interval."""
    return
        

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
            datetime=recording_time,
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
        classification_probability: float = 0.4,
        detection_probability: float = 0.8,
    ) -> data.Detection:
        """Return a random detection."""
        return data.Detection(
            detection_probability=detection_probability,
            tags=[
                data.PredictedTag(
                    tag=data.Tag(
                        value=tag_value,
                        key=tag_key,
                    ),
                    classification_probability=classification_probability,
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



""" TESTS - RECORDING TIME INTERVAL - SAVING MANAGERS"""
def test_save_recording_ifin_interval(
        create_test_timeinterval,
        create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    time_interval = create_test_timeinterval(
        start_time=datetime.time(22, 0, 0),
        end_time=datetime.time(4, 0, 0),
    )
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 23, 0, 0),
    )

    saving_filter = saving_filters.SaveIfInInterval(interval=time_interval, timezone=datetime.timezone.utc)
    # Act
    result = saving_filter.should_save_recording(recording)

    # Check
    assert result == True

def test_delete_recording_ifnotin_interval(
        create_test_timeinterval,
        create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    time_interval = create_test_timeinterval(
        start_time=datetime.time(22, 0, 0),
        end_time=datetime.time(4, 0, 0),
    )
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 12, 0, 0),
    )

    saving_filter = saving_filters.SaveIfInInterval(interval=time_interval, timezone=datetime.timezone.utc)
    # Act
    result = saving_filter.should_save_recording(recording)

    # Check
    assert result == False


def test_before_dawndusk_time_interval(
        create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    interval_duration: float = 20 # in minutes
    timezone = pytz.timezone("Europe/London")

    saving_filter = saving_filters.Before_DawnDuskTimeInterval(duration=interval_duration, timezone=timezone)

    # Fetch sun information
    test_date = datetime.datetime(2024, 8, 1, tzinfo=timezone)
    sun_info = sun(LocationInfo(str(timezone)).observer, date=test_date, tzinfo=timezone)
    dawntime = sun_info["dawn"]
    print(f"DawnTime: {dawntime}")
    dusktime = sun_info["dusk"]

    # Case 1: Recording exactly at dawn
    recording_at_dawn = create_test_recording(recording_time=datetime.datetime(2024, 8, 1, 4, 30, 0))
    assert saving_filter.should_save_recording(recording_at_dawn) is True

    # Case 2: Recording within the interval before dawn
    recording_inside_dawninterval = create_test_recording(dawntime - datetime.timedelta(minutes=10))
    assert saving_filter.should_save_recording(recording_inside_dawninterval) is True

    # Case 3: Recording outside the interval before dawn
    recording_outside_dawninterval = create_test_recording(dawntime - datetime.timedelta(minutes=40))
    assert saving_filter.should_save_recording(recording_outside_dawninterval) is False

def test_delete_recording_before_dawndusk_outsideinterval(
        create_test_recording,
) -> None:
    """Test if a recording is saved if it is in the interval."""
    # Setup
    interval_duration: float = 5 # in minutes 
    timezone = datetime.timezone.utc

    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 21, 0, 0),
    )

    saving_filter = saving_filters.Before_DawnDuskTimeInterval(duration=interval_duration, timezone=datetime.timezone.utc)
    # Act
    result = saving_filter.should_save_recording(recording)

    # Check
    assert result == False



""" TESTS - THRESHOLD DETECTIONS - SAVING FILTERS """
def test_delete_recording_without_detections(
    create_test_recording,
    create_test_model_output,
) -> None:
    """Test if the recording is deleted if it has no detections."""
    # Setup
    saving_threshold = 0.6
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
    )
    model_output = create_test_model_output(
        detections=[]
    )

    saving_filter = saving_filters.ThresholdDetectionSavingRecordingFilter(
        saving_threshold=saving_threshold
    )
    # Act
    result = saving_filter.should_save_recording(recording, model_outputs=[model_output])

    # Check
    assert result == False 


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
                classification_probability = 0.7,
                detection_probability = 0.8,
            ),
            create_test_detection(
                tag_value="species_2",
                classification_probability = 0.8,
                detection_probability = 0.9,
            )
        ]
    )

    saving_filter = saving_filters.ThresholdDetectionSavingRecordingFilter(saving_threshold=saving_threshold)
    # Act
    result = saving_filter.should_save_recording(recording, model_outputs=[model_output])

    # Check
    assert result == True


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
                classification_probability = 0.4,
                detection_probability = 0.8,
            ),
            create_test_detection(
                tag_value="species_2",
                classification_probability = 0.3,
                detection_probability = 0.7,
            )
        ]
    )

    saving_filter = saving_filters.ThresholdDetectionSavingRecordingFilter(saving_threshold=saving_threshold)
    # Act
    result = saving_filter.should_save_recording(recording, model_outputs=[model_output])

    # Check
    assert result == True


def test_delete_recording_if_detclassprob_below_savingthreshold(
        create_test_model_output,
        create_test_recording,
        create_test_detection,
) -> None:
    """Test if the recording is deleted if none of the probabilities are above the saving threshold."""
    # Setup
    saving_threshold = 0.6
    recording = create_test_recording(
        recording_time=datetime.datetime(2024, 8, 1, 20, 0, 0),
    )
    model_output = create_test_model_output(
        detections=[
            create_test_detection(
                tag_value="species_1",
                classification_probability = 0.4,
                detection_probability = 0.5,
            ),
            create_test_detection(
                tag_value="species_2",
                classification_probability = 0.3,
                detection_probability = 0.4,
            )
        ]
    )

    saving_filter = saving_filters.ThresholdDetectionSavingRecordingFilter(saving_threshold=saving_threshold)
    # Act
    result = saving_filter.should_save_recording(recording, model_outputs=[model_output])
    
    # Check
    assert result == False



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
                classification_probability=0.4,
                detection_probability=0.8,
            ),
            create_test_detection(
                tag_value="species_2",
                classification_probability=0.3,
                detection_probability=0.7,
            ),
        ]
    )

    saving_filter = saving_filters.FocusTagValueSavingRecordingFilter(values=focus_species)
    # Act
    result = saving_filter.should_save_recording(recording, model_outputs=[model_output])

    # Check
    assert result == True


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
                classification_probability=0.4,
                detection_probability=0.8,
            ),
            create_test_detection(
                tag_value="species_4",
                classification_probability=0.3,
                detection_probability=0.7,
            ),
        ]
    )

    saving_filter = saving_filters.FocusTagValueSavingRecordingFilter(values=focus_species)
    # Act
    result = saving_filter.should_save_recording(recording, model_outputs=[model_output])

    # Check
    assert result == False



""" TESTS - FOCUS TAGS - SAVING FILTERS """



