"""Test the recording of an audio files."""

import math
import wave
from pathlib import Path

import guano
import pytest

from acoupi import data
from acoupi.components.audio_recorder.pipewire_recorder import PWRecorder
from acoupi.devices.audio.pipewire import (
    get_default_microphone,
    has_input_audio_device,
)
from acoupi.system.exceptions import HealthCheckError
from acoupi.tasks.recording import add_guano_metadata


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_audio_recording(deployment: data.Deployment, tmp_path: Path):
    """Test getting information from microhpone."""
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    audio_channels = device.max_input_channels
    device_name = device.name
    recorder = PWRecorder(
        duration=0.1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name=device_name,
        audio_dir=tmp_path,
    )

    # record audio
    recording = recorder.record(deployment=deployment)
    assert isinstance(recording, data.Recording)
    assert recording.deployment == deployment
    assert recording.duration == 0.1
    assert recording.samplerate == samplerate
    assert recording.audio_channels == audio_channels
    assert recording.path is not None
    assert recording.path.exists()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_is_succesful(tmp_path: Path):
    """Test check_is_succesful."""
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    audio_channels = device.max_input_channels
    device_name = device.name
    recorder = PWRecorder(
        duration=0.1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name=device_name,
        audio_dir=tmp_path,
    )

    # If everything is ok, the check should pass
    recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_fails_if_audio_device_is_not_found(tmp_path: Path):
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    audio_channels = device.max_input_channels
    recorder = PWRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name="invalid_device",
        audio_dir=tmp_path,
    )

    with pytest.raises(HealthCheckError, match="device"):
        recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_check_fails_if_invalid_number_of_audio_channels(tmp_path: Path):
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    device_name = device.name
    recorder = PWRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=1000,
        device_name=device_name,
        audio_dir=tmp_path,
    )

    with pytest.raises(HealthCheckError, match="channels"):
        recorder.check()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
@pytest.mark.parametrize("duration", [0.1, 0.3, 0.7, 1])
def test_recording_duration_is_as_requested(
    tmp_path: Path,
    duration: float,
    deployment: data.Deployment,
):
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    device_name = device.name
    recorder = PWRecorder(
        duration=duration,
        samplerate=samplerate,
        audio_channels=1,
        device_name=device_name,
        audio_dir=tmp_path,
    )

    recording = recorder.record(deployment=deployment)

    assert recording.path is not None
    with wave.open(str(recording.path)) as wf:
        assert samplerate == wf.getframerate()
        assert math.isclose(
            duration,
            wf.getnframes() / samplerate,
            abs_tol=0.01,
        )


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_can_record_with_time_expansion(
    tmp_path: Path, deployment: data.Deployment
):
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    device_name = device.name
    recorder = PWRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=1,
        device_name=device_name,
        audio_dir=tmp_path,
        time_expansion=0.1,
    )

    recording = recorder.record(deployment=deployment)

    # The recording object has the original samplerate
    assert recording.samplerate == samplerate
    assert recording.time_expansion == 0.1

    with wave.open(str(recording.path)) as wf:
        stored_samplerate = wf.getframerate()
        assert math.isclose(
            stored_samplerate,
            recorder.get_expanded_samplerate(),
            abs_tol=0.01,
        )


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No audio device found.",
)
def test_time_expansion_is_saved_in_guano_metadata(
    tmp_path: Path, deployment: data.Deployment, mocker
):
    mocker.patch(
        "acoupi.tasks.recording.get_rpi_serial_number",
        return_value="1234567890ABCDEF",
    )

    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48000
    device_name = device.name
    recorder = PWRecorder(
        duration=1,
        samplerate=samplerate,
        audio_channels=1,
        device_name=device_name,
        audio_dir=tmp_path,
        time_expansion=0.1,
    )

    recording = recorder.record(deployment=deployment)

    add_guano_metadata(recording)

    assert recording.path is not None
    g = guano.GuanoFile(str(recording.path))
    assert g["TE"] == str(0.1)
    assert g["Samplerate"] == samplerate
