from typing import List, Tuple

import pyaudio
from pydantic import BaseModel


class DeviceInfo(BaseModel):
    """A dataclass to store the information of an audio device."""

    index: int
    """The input index of the audio device."""

    name: str
    """The name of the audio device."""

    max_input_channels: int
    """The maximum number of input channels."""

    default_samplerate: float
    """The default samplerate of the audio device."""


def get_input_devices(p: pyaudio.PyAudio) -> List[DeviceInfo]:
    """Get all input devices available."""
    count = p.get_device_count()

    devices = []
    for i in range(count):
        info = p.get_device_info_by_index(i)

        if int(info["maxInputChannels"]) > 0:
            devices.append(
                DeviceInfo.model_validate(
                    {
                        "index": i,
                        "name": info["name"],
                        "max_input_channels": info["maxInputChannels"],
                        "default_samplerate": info["defaultSampleRate"],
                    }
                )
            )

    return devices


def has_input_audio_device() -> bool:
    """Check if there are any input audio devices available."""
    p = pyaudio.PyAudio()

    try:
        p.get_default_input_device_info()
        return True
    except IOError:
        return False


def get_default_microphone() -> Tuple[int, int, str]:
    """Check if there are any input audio devices available.

    And get the information of a compatible audio device.

    Returns
    -------
    channels: int
        The number of audio channels of the audio device.
    sample_rate: int
        The samplerate of the audio device.
    device_name: str
        The name of the audio device.

    Raises
    ------
    IOError
        If no compatible audio device is found.
    """

    # Create an instance of PyAudio
    p = pyaudio.PyAudio()
    try:
        p.get_default_input_device_info()

        # Get default input device info
        default_input_device = p.get_default_input_device_info()

        # Get the number of channels
        channels = int(default_input_device["maxInputChannels"])

        # Get the input device name
        name = str(default_input_device["name"])

        # Get the sample rate
        sample_rate = int(default_input_device["defaultSampleRate"])

        p.terminate()
        return channels, sample_rate, name

    except IOError:
        raise IOError("No compatible audio device found.")
