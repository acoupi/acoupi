import json
from subprocess import CalledProcessError

import pytest

from acoupi.devices.audio.pipewire import (
    DeviceInfo,
    get_default_microphone,
    get_input_device_by_name,
    get_input_devices,
    has_input_audio_device,
)
from acoupi.system.exceptions import DeviceUnavailableError


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

    def test_raises_error_if_pw_dump_is_missing(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr("acoupi.devices.audio.pipewire.run", raise_error)

        with pytest.raises(
            DeviceUnavailableError, match="pw-dump command was not found"
        ):
            get_input_devices()

    def test_raise_error_if_pw_dump_fails(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise CalledProcessError(
                1, ["pw-dump"], stderr="service unavailable"
            )

        monkeypatch.setattr("acoupi.devices.audio.pipewire.run", raise_error)

        with pytest.raises(
            DeviceUnavailableError, match="service unavailable"
        ):
            get_input_devices()

    def test_parses_enumformat_choice_objects_and_aggregates_channels(
        self, monkeypatch, make_completed_process
    ):
        payload = [
            {
                "id": 60,
                "type": "PipeWire:Interface:Node",
                "info": {
                    "props": {
                        "media.class": "Audio/Source",
                        "node.name": "alsa_input.usb-test_device.analog-surround-51",
                        "node.description": "Test Device",
                    },
                    "params": {
                        "EnumFormat": [
                            {
                                "mediaType": "audio",
                                "mediaSubtype": "raw",
                                "rate": {
                                    "default": 48000,
                                    "min": 44100,
                                    "max": 96000,
                                },
                                "channels": {
                                    "default": 1,
                                    "min": 1,
                                    "max": 1,
                                },
                            },
                            {
                                "mediaType": "audio",
                                "mediaSubtype": "raw",
                                "rate": 192000,
                                "channels": {
                                    "default": 6,
                                    "min": 2,
                                    "max": 6,
                                },
                            },
                        ]
                    },
                },
            }
        ]
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        devices = get_input_devices()

        assert len(devices) == 1
        assert devices[0].max_input_channels == 6
        assert sorted(devices[0].samplerates) == [44100, 48000, 96000, 192000]


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

    def test_raises_if_device_is_missing(
        self, monkeypatch, load_audio_test_fixture, make_completed_process
    ):
        payload = load_audio_test_fixture("pipewire/dumps/mixed_sources.json")
        monkeypatch.setattr(
            "acoupi.devices.audio.pipewire.run",
            lambda *args, **kwargs: make_completed_process(
                json.dumps(payload)
            ),
        )

        with pytest.raises(DeviceUnavailableError, match="not found"):
            get_input_device_by_name("missing-device")

    def test_raises_if_pw_dump_fails(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr("acoupi.devices.audio.pipewire.run", raise_error)

        with pytest.raises(
            DeviceUnavailableError, match="pw-dump command was not found"
        ):
            get_input_device_by_name("missing-device")


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

    def test_returns_false_when_no_source_device_exists(
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

        assert has_input_audio_device() is False

    def test_returns_false_when_pw_dump_fails(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr("acoupi.devices.audio.pipewire.run", raise_error)

        assert has_input_audio_device() is False


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
