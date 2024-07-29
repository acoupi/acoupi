from acoupi.devices import audio

TEST_DEVICE_INFO = [
    {
        "index": 0,
        "structVersion": 2,
        "name": "bcm2835 Headphones: - (hw:0,0)",
        "hostApi": 0,
        "maxInputChannels": 0,
        "maxOutputChannels": 8,
        "defaultLowInputLatency": -1.0,
        "defaultLowOutputLatency": 0.0016099773242630386,
        "defaultHighInputLatency": -1.0,
        "defaultHighOutputLatency": 0.034829931972789115,
        "defaultSampleRate": 44100.0,
    },
    {
        "index": 1,
        "structVersion": 2,
        "name": "vc4-hdmi-1: MAI PCM i2s-hifi-0 (hw:2,0)",
        "hostApi": 0,
        "maxInputChannels": 0,
        "maxOutputChannels": 2,
        "defaultLowInputLatency": -1.0,
        "defaultLowOutputLatency": 0.005804988662131519,
        "defaultHighInputLatency": -1.0,
        "defaultHighOutputLatency": 0.034829931972789115,
        "defaultSampleRate": 44100.0,
    },
    {
        "index": 2,
        "structVersion": 2,
        "name": "UltraMic 250K 16 bit r4: USB Audio (hw:3,0)",
        "hostApi": 0,
        "maxInputChannels": 1,
        "maxOutputChannels": 0,
        "defaultLowInputLatency": 0.001048,
        "defaultLowOutputLatency": -1.0,
        "defaultHighInputLatency": 0.006144,
        "defaultHighOutputLatency": -1.0,
        "defaultSampleRate": 250000.0,
    },
    {
        "index": 3,
        "structVersion": 2,
        "name": "sysdefault",
        "hostApi": 0,
        "maxInputChannels": 0,
        "maxOutputChannels": 128,
        "defaultLowInputLatency": -1.0,
        "defaultLowOutputLatency": 0.0016099773242630386,
        "defaultHighInputLatency": -1.0,
        "defaultHighOutputLatency": 0.034829931972789115,
        "defaultSampleRate": 44100.0,
    },
    {
        "index": 4,
        "structVersion": 2,
        "name": "default",
        "hostApi": 0,
        "maxInputChannels": 0,
        "maxOutputChannels": 128,
        "defaultLowInputLatency": -1.0,
        "defaultLowOutputLatency": 0.0016099773242630386,
        "defaultHighInputLatency": -1.0,
        "defaultHighOutputLatency": 0.034829931972789115,
        "defaultSampleRate": 44100.0,
    },
    {
        "index": 5,
        "structVersion": 2,
        "name": "dmix",
        "hostApi": 0,
        "maxInputChannels": 0,
        "maxOutputChannels": 2,
        "defaultLowInputLatency": -1.0,
        "defaultLowOutputLatency": 0.021333333333333333,
        "defaultHighInputLatency": -1.0,
        "defaultHighOutputLatency": 0.021333333333333333,
        "defaultSampleRate": 48000.0,
    },
]


class MockPyAudio:
    def get_device_count(self):
        return len(TEST_DEVICE_INFO)

    def get_device_info_by_index(self, index):
        return TEST_DEVICE_INFO[index]


def test_can_get_all_input_devices():
    p = MockPyAudio()

    # Act
    available_devices = audio.get_input_devices(p)  # type: ignore

    # Assert
    assert len(available_devices) == 1

    device = available_devices[0]

    assert device.index == 2
    assert device.name == "UltraMic 250K 16 bit r4"


def test_can_get_device_by_name():
    p = MockPyAudio()

    # Act
    device = audio.get_input_device_by_name(p, "UltraMic 250K 16 bit r4")  # type: ignore

    # Assert
    assert device.index == 2
    assert device.name == "UltraMic 250K 16 bit r4"
