"""Tests for the PipeWire audio recorder."""

import wave
from pathlib import Path

import pytest

from acoupi import data
from acoupi.components.audio_recorder.pipewire_recorder import PWRecorder
from acoupi.devices.audio.pipewire import (
    get_default_microphone,
    has_input_audio_device,
)
from acoupi.system.exceptions import (
    DeviceUnavailableError,
    HealthCheckError,
    RecordingError,
)


def create_wav_file(
    path: Path,
    samplerate: int,
    channels: int,
    frames: int,
) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(b"\x00\x00" * frames * channels)


def test_audio_recording(
    deployment: data.Deployment, tmp_path: Path, monkeypatch
):
    recorder = PWRecorder(
        duration=0.1,
        samplerate=48_000,
        audio_channels=1,
        device_name="test-mic",
        audio_dir=tmp_path,
    )

    monkeypatch.setattr(
        recorder,
        "generate_recording",
        lambda path: create_wav_file(path, 48_000, 1, 4_800),
    )

    recording = recorder.record(deployment=deployment)

    assert isinstance(recording, data.Recording)
    assert recording.deployment == deployment
    assert recording.duration == 0.1
    assert recording.samplerate == 48_000
    assert recording.audio_channels == 1
    assert recording.path is not None
    assert recording.path.exists()


@pytest.mark.skipif(
    not has_input_audio_device(),
    reason="No PipeWire input audio device found.",
)
def test_can_record_with_default_pipewire_input_device(
    deployment: data.Deployment,
    tmp_path: Path,
):
    device = get_default_microphone()
    samplerate = device.samplerates[0] if device.samplerates else 48_000
    audio_channels = min(device.max_input_channels, 1)
    recorder = PWRecorder(
        duration=0.1,
        samplerate=samplerate,
        audio_channels=audio_channels,
        device_name=device.name,
        audio_dir=tmp_path,
    )

    recording = recorder.record(deployment=deployment)

    assert recording.path is not None
    assert recording.path.exists()

    with wave.open(str(recording.path), "rb") as wf:
        assert wf.getframerate() == samplerate
        assert wf.getnchannels() == audio_channels
        assert wf.getnframes() == int(recording.duration * samplerate)


def test_check_detects_missing_pipewire_command(tmp_path: Path, monkeypatch):
    recorder = PWRecorder(
        duration=1,
        samplerate=48_000,
        audio_channels=1,
        device_name="test-mic",
        audio_dir=tmp_path,
    )

    def raise_error(self, path: Path, duration: float | None = None) -> None:
        raise DeviceUnavailableError(
            message="The pw-record command was not found.",
        )

    monkeypatch.setattr(
        "acoupi.components.audio_recorder.pipewire_recorder.PWRecorder.generate_recording",
        raise_error,
    )

    with pytest.raises(
        HealthCheckError, match="pw-record command was not found"
    ):
        recorder.check()


def test_check_detects_missing_device(tmp_path: Path, monkeypatch):
    recorder = PWRecorder(
        duration=1,
        samplerate=48_000,
        audio_channels=1,
        device_name="missing-device",
        audio_dir=tmp_path,
    )

    def raise_error(self, path: Path, duration: float | None = None) -> None:
        raise RecordingError(
            message="PipeWire failed to record audio",
            help="Check that the selected microphone exists.",
        )

    monkeypatch.setattr(
        "acoupi.components.audio_recorder.pipewire_recorder.PWRecorder.generate_recording",
        raise_error,
    )

    with pytest.raises(HealthCheckError, match="failed to record audio"):
        recorder.check()


def test_check_detects_invalid_configuration(tmp_path: Path, monkeypatch):
    recorder = PWRecorder(
        duration=1,
        samplerate=48_000,
        audio_channels=99,
        device_name="test-mic",
        audio_dir=tmp_path,
    )

    def raise_error(self, path: Path, duration: float | None = None) -> None:
        raise RecordingError(
            message="PipeWire failed to record audio",
            help="Check that the selected microphone exists and supports the requested settings.",
        )

    monkeypatch.setattr(
        "acoupi.components.audio_recorder.pipewire_recorder.PWRecorder.generate_recording",
        raise_error,
    )

    with pytest.raises(HealthCheckError, match="failed to record audio"):
        recorder.check()


def test_check_succeeds_only_with_expected_recording_output(
    tmp_path: Path, monkeypatch
):
    recorder = PWRecorder(
        duration=1,
        samplerate=48_000,
        audio_channels=2,
        device_name="test-mic",
        audio_dir=tmp_path,
    )

    calls = {}

    def mock_generate_recording(
        self, path: Path, duration: float | None = None
    ) -> None:
        calls.update(
            path=path,
            duration=duration,
            samplerate=recorder.samplerate,
            audio_channels=recorder.audio_channels,
            device_name=recorder.device_name,
        )
        create_wav_file(
            path,
            samplerate=recorder.samplerate,
            channels=recorder.audio_channels,
            frames=int((duration or recorder.duration) * recorder.samplerate),
        )

    monkeypatch.setattr(
        "acoupi.components.audio_recorder.pipewire_recorder.PWRecorder.generate_recording",
        mock_generate_recording,
    )

    recorder.check()

    assert calls["path"].name == "recording.wav"
    assert calls["duration"] == 0.1
    assert calls["samplerate"] == 48_000
    assert calls["audio_channels"] == 2
    assert calls["device_name"] == "test-mic"
