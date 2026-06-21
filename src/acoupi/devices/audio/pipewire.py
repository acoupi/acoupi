import json
from subprocess import CalledProcessError, run

from pydantic import BaseModel

__all__ = [
    "get_input_devices",
]


class DeviceInfo(BaseModel):
    """A dataclass to store the information of an audio device."""

    description: str
    """The input index of the audio device."""

    name: str
    """The name of the audio device."""

    max_input_channels: int
    """The maximum number of input channels."""

    samplerates: list[int]
    """Listed supported sampling rates"""


def get_input_devices() -> list[DeviceInfo]:
    try:
        result = run(["pw-dump"], capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise RuntimeError(
            "The pw-dump command was not found. ",
            "Install PipeWire tools and check that pw-dump is on PATH.",
        ) from error
    except CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        raise RuntimeError(
            "Failed to query PipeWire devices"
            + (f": {stderr}" if stderr else "."),
            "Check that PipeWire is running and accessible.",
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
    available_devices = get_input_devices()

    for device in available_devices:
        if device.name == name:
            return device

    raise IOError(
        f"Audio device with name '{name}' not found."
        f" Available devices: {', '.join([device.name for device in available_devices])}"
    )


def has_input_audio_device() -> bool:
    try:
        return bool(get_input_devices())
    except RuntimeError:
        return False


def get_default_microphone() -> DeviceInfo:
    available_devices = get_input_devices()

    if not available_devices:
        raise IOError("No compatible audio devices found.")

    return available_devices[0]
