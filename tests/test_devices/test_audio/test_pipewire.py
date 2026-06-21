import json
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, TimeoutExpired

import pytest

from acoupi.components.audio_recorder.pipewire_recorder import PWRecorder
from acoupi.devices.audio.pipewire import (
    DeviceInfo,
    get_default_microphone,
    get_input_device_by_name,
    get_input_devices,
    has_input_audio_device,
)
from acoupi.system.exceptions import ParameterError


class TestGetInputDevices:
    def test_returns_only_audio_source_nodes(
        self, monkeypatch, load_audio_test_fixture, make_completed_process
    ):
        payload = load_audio_test_fixture("pipewire/dumps/mixed_sources.json")
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        devices = get_input_devices()

        assert len(devices) == 2
        assert all(isinstance(device, DeviceInfo) for device in devices)
        assert (
            devices[0].name
            == "alsa_input.usb-UltraMic_250K_16_bit_r4-00.mono-fallback"
        )
        assert devices[0].description == "UltraMic 250K 16 bit r4 Mono"
        assert devices[0].max_input_channels == 1
        assert sorted(devices[0].samplerates) == [192000, 250000]
        assert (
            devices[1].name
            == "alsa_input.usb-Focusrite_Scarlett_2i2_USB-00.analog-stereo"
        )
        assert devices[1].max_input_channels == 2
        assert sorted(devices[1].samplerates) == [48000, 96000]

    def test_returns_empty_list_when_no_audio_sources(
        self, monkeypatch, load_audio_test_fixture, make_completed_process
    ):
        payload = load_audio_test_fixture(
            "pipewire/dumps/no_audio_sources.json"
        )
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        assert get_input_devices() == []

    def test_raises_runtime_error_if_pw_dump_is_missing(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr("acoupi.devices.audio.pipewire.run", raise_error)

        with pytest.raises(
            RuntimeError, match="pw-dump command was not found"
        ):
            get_input_devices()

    def test_raises_runtime_error_if_pw_dump_fails(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise CalledProcessError(
                1, ["pw-dump"], stderr="service unavailable"
            )

        monkeypatch.setattr("acoupi.devices.audio.pipewire.run", raise_error)

        with pytest.raises(RuntimeError, match="service unavailable"):
            get_input_devices()


class TestGetInputDeviceByName:
    def test_returns_matching_device(
        self, monkeypatch, load_audio_test_fixture, make_completed_process
    ):
        payload = load_audio_test_fixture("pipewire/dumps/mixed_sources.json")
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        device = get_input_device_by_name(
            "alsa_input.usb-Focusrite_Scarlett_2i2_USB-00.analog-stereo"
        )

        assert device.description == "Scarlett 2i2 USB"
        assert device.max_input_channels == 2


class TestHasInputAudioDevice:
    def test_returns_true_when_source_device_exists(
        self, monkeypatch, load_audio_test_fixture, make_completed_process
    ):
        payload = load_audio_test_fixture("pipewire/dumps/mixed_sources.json")
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        assert has_input_audio_device() is True


class TestGetDefaultMicrophone:
    def test_returns_first_available_input_device(
        self, monkeypatch, load_audio_test_fixture, make_completed_process
    ):
        payload = load_audio_test_fixture("pipewire/dumps/mixed_sources.json")
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        device = get_default_microphone()

        assert (
            device.name
            == "alsa_input.usb-UltraMic_250K_16_bit_r4-00.mono-fallback"
        )


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
            ParameterError, match="pw-record command was not found"
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
            ParameterError, match="did not finish within the expected time"
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

        with pytest.raises(ParameterError, match="failed to record audio"):
            recorder.generate_recording(tmp_path / "recording.wav")
