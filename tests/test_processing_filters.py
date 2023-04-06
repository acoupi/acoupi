"""Test acoupi processing filters."""
import datetime

from acoupi import processing_filters, types


def test_trivial_processing_filter():
    """Test trivial processing filter."""
    filter = processing_filters.TrivialProcessingFilter()
    recording = types.Recording(
        path="test",
        duration=1,
        samplerate=16000,
        datetime=datetime.datetime.now(),
    )
    assert filter.should_process_recording(recording) is True
