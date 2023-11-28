"""Test the recording of an audio files."""
from pathlib import Path
from acoupi import components, data


def test_audio_recording(deployment: data.Deployment, tmp_path: Path):
    """Test the audio file recording."""
    recorder = components.PyAudioRecorder(
        duration=0.1,
        samplerate=8000,
        audio_channels=1,
        audio_dir=tmp_path,
    )

    # record audio
    recording = recorder.record(deployment=deployment)
    assert isinstance(recording, data.Recording)
    assert recording.deployment == deployment
    assert recording.duration == 0.1
    assert recording.samplerate == 8000
    assert recording.audio_channels == 1
    assert recording.path is not None
    assert recording.path.exists()
