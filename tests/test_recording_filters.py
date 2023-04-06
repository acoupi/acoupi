"""Test acoupi recording filters."""
import datetime

from acoupi import recording_filters, types


def test_negative_recording_filter():
    """Test negative recording filter."""
    filter = recording_filters.NegativeRecordingFilter()
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = []
    assert not filter.should_keep_recording(recording, detections)


def test_positive_recording_filter():
    """Test positive recording filter."""
    filter = recording_filters.PositiveRecordingFilter()
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = []
    assert filter.should_keep_recording(recording, detections)


def test_threshold_recording_filter_rejects_recordings_without_detections():
    """Test threshold recording filter rejects recordings without detections."""
    filter = recording_filters.ThresholdRecordingFilter(threshold=0.5)
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = []
    assert not filter.should_keep_recording(recording, detections)


def test_threshold_recording_filter_rejects_low_confidence_recordings():
    """Test threshold recording filter rejects recordings correctly.

    It should reject recordings with detections with a probability below the
    provided threshold.
    """
    filter = recording_filters.ThresholdRecordingFilter(threshold=0.5)
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.4,
        )
    ]
    assert not filter.should_keep_recording(recording, detections)


def test_threshold_recording_filter_keeps_high_confidence_recordings():
    """Test threshold recording filter keeps recordings correctly.

    It should keep recordings with detections with a probability above the
    provided threshold.
    """
    filter = recording_filters.ThresholdRecordingFilter(threshold=0.5)
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.6,
        )
    ]
    assert filter.should_keep_recording(recording, detections)


def test_threshold_recording_filter_with_multiple_detections():
    """Test threshold recording filter keeps recordings correctly.

    It should keep recordings with detections with a probability above the
    provided threshold.
    """
    filter = recording_filters.ThresholdRecordingFilter(threshold=0.5)
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.4,
        ),
        types.Detection(
            species_name="test",
            probability=0.6,
        ),
    ]
    assert filter.should_keep_recording(recording, detections)

    filter = recording_filters.ThresholdRecordingFilter(threshold=0.7)
    detections = [
        types.Detection(
            species_name="test",
            probability=0.4,
        ),
        types.Detection(
            species_name="test",
            probability=0.6,
        ),
    ]
    assert not filter.should_keep_recording(recording, detections)


def test_focus_species_filter_rejects_recordings_without_detections():
    """Test focus species recording filter rejects recordings without detections."""
    filter = recording_filters.FocusSpeciesRecordingFilter(species=["test"])
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = []
    assert not filter.should_keep_recording(recording, detections)


def test_focus_species_filter_rejects_if_no_target_species_found():
    """Test focus species recording filter rejects if no target species found."""
    filter = recording_filters.FocusSpeciesRecordingFilter(species=["test"])
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test2",
            probability=0.6,
        )
    ]
    assert not filter.should_keep_recording(recording, detections)


def test_focus_species_filter_rejects_low_confidence_detections():
    """Test focus species recording filter rejects low confidence detections."""
    filter = recording_filters.FocusSpeciesRecordingFilter(
        species=["test"], threshold=0.5
    )
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.4,
        )
    ]
    assert not filter.should_keep_recording(recording, detections)


def test_focus_species_filter_keeps_high_confidence_detections():
    """Test focus species recording filter keeps high confidence detections."""
    filter = recording_filters.FocusSpeciesRecordingFilter(
        species=["test"], threshold=0.5
    )
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.6,
        )
    ]
    assert filter.should_keep_recording(recording, detections)


def test_focus_species_filter_rejects_even_with_confident_non_target():
    """Test focus species recording filter rejects correctly.

    Even in the case with confident non-target detections.
    """
    filter = recording_filters.FocusSpeciesRecordingFilter(
        species=["test"], threshold=0.5
    )
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.4,
        ),
        types.Detection(
            species_name="test2",
            probability=0.6,
        ),
    ]
    assert not filter.should_keep_recording(recording, detections)


def test_focus_species_filter_keeps_with_at_least_one_target_species():
    """Test focus species recording filter keeps correctly.

    It should keep recordings with at least one target species detection
    with a probability above the provided threshold.
    """
    filter = recording_filters.FocusSpeciesRecordingFilter(
        species=["test", "test2"],
        threshold=0.5,
    )
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    detections = [
        types.Detection(
            species_name="test",
            probability=0.6,
        ),
        types.Detection(
            species_name="test2",
            probability=0.4,
        ),
    ]
    assert filter.should_keep_recording(recording, detections)
