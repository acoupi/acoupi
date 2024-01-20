"""Test the recording of an audio files."""
from pathlib import Path

import pytest

from acoupi import components, data

# from acoupi.components.audio_recorder import has_input_audio_device
from acoupi.components.audio_recorder import (
    get_default_microphone,
    has_input_audio_device,
)


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_audio_recording(deployment: data.Deployment, tmp_path: Path):
    """Test getting information from microhpone."""
    audio_channels, samplerate, device_name = get_default_microphone()
    recorder = components.PyAudioRecorder(
        duration=0.1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name=device_name,
        chunksize=4096,
        audio_dir=tmp_path,
    )

    # record audio
    recording = recorder.record(deployment=deployment)
    assert isinstance(recording, data.Recording)
    assert recording.deployment == deployment
    assert recording.duration == 0.1
    assert recording.samplerate == samplerate
    assert recording.audio_channels == audio_channels
    assert recording.chunksize == 4096
    assert recording.path is not None
    assert recording.path.exists()
