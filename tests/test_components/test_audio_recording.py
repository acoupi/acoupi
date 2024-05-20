"""Test the recording of an audio files."""

from pathlib import Path

import pytest

from acoupi import components, data
from acoupi.devices.audio import get_default_microphone, has_input_audio_device
from acoupi.system.exceptions import HealthCheckError


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
        chunksize=8192,
        audio_dir=tmp_path,
    )

    # record audio
    recording = recorder.record(deployment=deployment)
    assert isinstance(recording, data.Recording)
    assert recording.deployment == deployment
    assert recording.duration == 0.1
    assert recording.samplerate == samplerate
    assert recording.audio_channels == audio_channels
    assert recording.chunksize == 8192
    assert recording.path is not None
    assert recording.path.exists()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_is_succesful(tmp_path: Path):
    """Test check_is_succesful"""
    audio_channels, samplerate, device_name = get_default_microphone()
    recorder = components.PyAudioRecorder(
        duration=0.1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name=device_name,
        chunksize=8192,
        audio_dir=tmp_path,
    )

    # If everything is ok, the check should pass
    recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_fails_if_recording_duration_is_zero(
    monkeypatch, tmp_path: Path
):
    audio_channels, samplerate, device_name = get_default_microphone()
    recorder = components.PyAudioRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name=device_name,
        chunksize=8192,
        audio_dir=tmp_path,
    )

    def mock_get_recording_data(*args, **kwargs) -> bytes:
        return b""

    monkeypatch.setattr(
        recorder,
        "get_recording_data",
        mock_get_recording_data,
    )

    # If the duration is zero, the check should fail
    with pytest.raises(HealthCheckError):
        recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_fails_if_invalid_samplerate(tmp_path: Path):
    audio_channels, _, device_name = get_default_microphone()
    recorder = components.PyAudioRecorder(
        duration=1,
        samplerate=10,
        audio_channels=audio_channels,
        device_name=device_name,
        chunksize=8192,
        audio_dir=tmp_path,
    )

    # If the samplerate is invalid, the check should fail
    with pytest.raises(HealthCheckError, match="samplerate"):
        recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_fails_if_audio_device_is_not_found(tmp_path: Path):
    audio_channels, samplerate, _ = get_default_microphone()
    recorder = components.PyAudioRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name="invalid_device",
        chunksize=8192,
        audio_dir=tmp_path,
    )

    with pytest.raises(HealthCheckError, match="device"):
        recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_fails_if_invalid_number_of_audio_channels(tmp_path: Path):
    _, samplerate, device_name = get_default_microphone()
    recorder = components.PyAudioRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=1000,
        device_name=device_name,
        chunksize=8192,
        audio_dir=tmp_path,
    )

    with pytest.raises(HealthCheckError, match="channels"):
        recorder.check()
