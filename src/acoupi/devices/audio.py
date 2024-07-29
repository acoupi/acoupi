from typing import List, Tuple

import pyaudio
from pydantic import BaseModel

__all__ = [
    "DeviceInfo",
    "get_input_devices",
    "get_input_device_by_name",
    "has_input_audio_device",
    "get_default_microphone",
]


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
                        "name": parse_device_name(str(info["name"])),
                        "max_input_channels": info["maxInputChannels"],
                        "default_samplerate": info["defaultSampleRate"],
                    }
                )
            )

    return devices


def parse_device_name(full_name: str) -> str:
    """Parse the name of an audio device.

    Notes
    -----
    PyAudio appends additional information to the name of the audio device
    in the form of "<name>: <additional_info>". This function removes the
    additional information and returns the name of the audio device.
    """
    return full_name.split(":")[0].strip()


def get_input_device_by_name(p: pyaudio.PyAudio, name: str) -> DeviceInfo:
    """Get an input device by its name.

    Parameters
    ----------
    p: pyaudio.PyAudio
        An instance of PyAudio.
    name: str
        The name of the audio device.

    Returns
    -------
    DeviceInfo
        The information of the audio device.

    Raises
    ------
    IOError
        If the audio device with the given name is not found.

    Notes
    -----
    It is assumed that the name of the audio device has been cleaned
    using the `parse_device_name` function, i.e., the additional information
    added by PyAudio has been removed. This should coincide with the name
    provided by `arecord -l` or `lsusb`.
    """
    avaliable_devices = get_input_devices(p)

    for device in avaliable_devices:
        if name == device.name:
            return device

    raise IOError(
        f"Audio device with name '{name}' not found."
        f" Available devices: {', '.join([device.name for device in avaliable_devices])}"
    )


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

    except IOError as e:
        raise IOError("No compatible audio device found.") from e
