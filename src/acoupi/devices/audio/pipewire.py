"""PipeWire device discovery helpers for audio input devices."""

import json
from subprocess import CalledProcessError, run

from pydantic import BaseModel

from acoupi.system.exceptions import DeviceUnavailableError

__all__ = [
    "get_input_devices",
]


class DeviceInfo(BaseModel):
    """Normalized description of a PipeWire audio input device."""

    description: str
    """The input index of the audio device."""

    name: str
    """The name of the audio device."""

    max_input_channels: int
    """The maximum number of input channels."""

    samplerates: list[int]
    """Listed supported sampling rates"""


def get_input_devices() -> list[DeviceInfo]:
    """Return all PipeWire audio input devices visible to the current session.

    Raises
    ------
    DeviceUnavailableError
        If PipeWire device information cannot be queried.
    """
    try:
        result = run(["pw-dump"], capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise DeviceUnavailableError(
            message="The pw-dump command was not found.",
            help="Install PipeWire tools and check that pw-dump is on PATH.",
        ) from error
    except CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        raise DeviceUnavailableError(
            message="Failed to query PipeWire devices"
            + (f": {stderr}" if stderr else "."),
            help="Check that PipeWire is running and accessible.",
        ) from error

    devices = json.loads(result.stdout)
    return [
        _parse_pw_info(info)
        for device in devices
        if device.get("type") == "PipeWire:Interface:Node"
        and (info := device.get("info")) is not None
        and info.get("props", {}).get("media.class") == "Audio/Source"
    ]


def _parse_pw_info(pw_info: dict) -> DeviceInfo:
    """Convert raw ``pw-dump`` node information into ``DeviceInfo``."""
    props = pw_info["props"]
    formats = pw_info["params"]["EnumFormat"]
    default_format = formats[0]
    return DeviceInfo(
        name=props["node.name"],
        description=props["node.description"],
        max_input_channels=default_format["channels"],
        samplerates=list({format.get("rate", 48_000) for format in formats}),
    )


def get_input_device_by_name(name: str) -> DeviceInfo:
    """Return a PipeWire input device by its normalized name.

    Raises
    ------
    DeviceUnavailableError
        If the named device cannot be found or devices cannot be queried.
    """
    available_devices = get_input_devices()

    for device in available_devices:
        if device.name == name:
            return device

    raise DeviceUnavailableError(
        message=(
            f"Audio device with name '{name}' not found."
            f" Available devices: {', '.join([device.name for device in available_devices])}"
        )
    )


def has_input_audio_device() -> bool:
    """Return ``True`` when at least one PipeWire input device is available."""
    try:
        return bool(get_input_devices())
    except DeviceUnavailableError:
        return False


def get_default_microphone() -> DeviceInfo:
    """Return the first available PipeWire input device.

    Raises
    ------
    DeviceUnavailableError
        If no compatible PipeWire input device is available.
    """
    available_devices = get_input_devices()

    if not available_devices:
        raise DeviceUnavailableError("No compatible audio devices found.")

    return available_devices[0]
