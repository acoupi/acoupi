"""Tests for the PipeWire audio recorder."""

import wave
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from acoupi import data
from acoupi.components.audio_recorder.pipewire_recorder import (
    PWRecorder,
    _parse_pw_microphone_config,
)
from acoupi.devices.audio.pipewire import DeviceInfo
from acoupi.devices.audio.pipewire import (
    get_default_microphone,
    has_input_audio_device,
)
from acoupi.system.exceptions import (
    DeviceUnavailableError,
    HealthCheckError,
    ParameterError,
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


class TestGenerateRecording:
    def test_creates_parent_dir(self, tmp_path: Path, monkeypatch):
        output_path = tmp_path / "nested" / "recording.wav"
        recorder = PWRecorder(
            duration=0.5,
            samplerate=48_000,
            audio_channels=2,
            device_name="test-mic",
            audio_dir=tmp_path,
        )
        run_calls = {}

        def mock_run(cmd, **kwargs):
            run_calls.update(cmd=cmd, timeout=kwargs["timeout"])
            output_path.touch()
            return CompletedProcess(
                args=["pw-record"],
                returncode=0,
                stdout="",
                stderr="",
            )

        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.run",
            mock_run,
        )

        assert not output_path.parent.exists()

        recorder.generate_recording(output_path)

        assert output_path.parent.exists()
        assert run_calls["cmd"] == [
            "pw-record",
            "--rate=48000",
            "--channels=2",
            "--sample-count=24000",
            "--target=test-mic",
            str(output_path),
        ]
        assert run_calls["timeout"] == 2.5

    def test_raises_if_command_missing(self, tmp_path: Path, monkeypatch):
        recorder = PWRecorder(
            duration=0.5,
            samplerate=48_000,
            audio_channels=1,
            device_name="test-mic",
            audio_dir=tmp_path,
        )

        def raise_error(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.run",
            raise_error,
        )

        with pytest.raises(
            DeviceUnavailableError, match="pw-record command was not found"
        ):
            recorder.generate_recording(tmp_path / "recording.wav")

    def test_raises_if_command_times_out(self, tmp_path: Path, monkeypatch):
        recorder = PWRecorder(
            duration=0.5,
            samplerate=48_000,
            audio_channels=1,
            device_name="test-mic",
            audio_dir=tmp_path,
        )

        def raise_error(*args, **kwargs):
            raise TimeoutExpired(cmd=["pw-record"], timeout=2.5)

        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.run",
            raise_error,
        )

        with pytest.raises(
            RecordingError, match="did not finish within the expected time"
        ):
            recorder.generate_recording(tmp_path / "recording.wav")

    def test_raises_if_output_is_missing(self, tmp_path: Path, monkeypatch):
        recorder = PWRecorder(
            duration=0.5,
            samplerate=48_000,
            audio_channels=1,
            device_name="test-mic",
            audio_dir=tmp_path,
        )

        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.run",
            lambda *args, **kwargs: CompletedProcess(
                args=["pw-record"],
                returncode=0,
                stdout="",
                stderr="",
            ),
        )

        with pytest.raises(RecordingError, match="failed to record audio"):
            recorder.generate_recording(tmp_path / "recording.wav")


class TestParsePWRecorderConfig:
    @staticmethod
    def build_ultramic_device() -> DeviceInfo:
        return DeviceInfo(
            name="alsa_input.usb-UltraMic_250K_16_bit_r4-00.mono-fallback",
            description="UltraMic 250K 16 bit r4 Mono",
            max_input_channels=1,
            samplerates=[192000, 250000],
        )

    def test_raises_parameter_error_if_device_name_missing_without_prompt(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.get_input_devices",
            lambda: [],
        )

        with pytest.raises(
            ParameterError, match="No microphone device name provided"
        ):
            _parse_pw_microphone_config([], prompt=False)

    def test_raises_parameter_error_if_device_name_is_unknown(
        self, monkeypatch
    ):
        ultramic = self.build_ultramic_device()
        scarlett = DeviceInfo(
            name="alsa_input.usb-Focusrite_Scarlett_2i2_USB-00.analog-stereo",
            description="Scarlett 2i2 USB",
            max_input_channels=2,
            samplerates=[48000, 96000],
        )
        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.get_input_devices",
            lambda: [ultramic, scarlett],
        )

        with pytest.raises(ParameterError, match="No device found with name"):
            _parse_pw_microphone_config(
                ["--device-name=missing-device"],
                prompt=False,
            )

    def test_raises_parameter_error_if_samplerate_missing_without_prompt(
        self, monkeypatch
    ):
        device = self.build_ultramic_device()
        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.get_input_devices",
            lambda: [device],
        )

        with pytest.raises(ParameterError, match="No samplerate provided"):
            _parse_pw_microphone_config(
                [
                    "--device-name=alsa_input.usb-UltraMic_250K_16_bit_r4-00.mono-fallback"
                ],
                prompt=False,
            )

    def test_raises_parameter_error_if_channels_missing_without_prompt(
        self, monkeypatch
    ):
        device = self.build_ultramic_device()
        monkeypatch.setattr(
            "acoupi.components.audio_recorder.pipewire_recorder.get_input_devices",
            lambda: [device],
        )

        with pytest.raises(ParameterError, match="No audio channels provided"):
            _parse_pw_microphone_config(
                [
                    "--device-name=alsa_input.usb-UltraMic_250K_16_bit_r4-00.mono-fallback",
                    "--samplerate=250000",
                ],
                prompt=False,
            )
