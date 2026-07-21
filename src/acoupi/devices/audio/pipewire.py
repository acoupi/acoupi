"""PipeWire device discovery helpers for audio input devices."""

import json
from subprocess import CalledProcessError, run
from typing import Literal

from pydantic import BaseModel, ConfigDict, TypeAdapter

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


class IntChoice(BaseModel):
    default: int
    min: int | None = None
    max: int | None = None
    step: int | None = None
    model_config = ConfigDict(extra="allow")


class FloatChoice(BaseModel):
    default: float
    min: float | None = None
    max: float | None = None
    step: float | None = None
    model_config = ConfigDict(extra="allow")


class StrChoice(BaseModel):
    default: str
    model_config = ConfigDict(extra="allow")


class BoolChoice(BaseModel):
    default: bool
    model_config = ConfigDict(extra="allow")


IntValue = int | IntChoice
FloatValue = float | FloatChoice
StrValue = str | StrChoice
BoolValue = bool | BoolChoice


class EnumFormatItem(BaseModel):
    mediaType: Literal["audio"]
    mediaSubtype: str

    format: StrValue | None = None
    rate: IntValue | None = None
    channels: IntValue | None = None
    position: list[str] | None = None

    model_config = ConfigDict(extra="allow")


DEFAULT_SAMPLERATE = 48000
DEFAULT_SAMPLERATE_CHOICES = [
    16000,
    32000,
    44100,
    48000,
    96000,
    192000,
]


def _extract_rate(rate_field: EnumFormatItem) -> list[int]:
    rate_info = rate_field.rate

    if isinstance(rate_info, int):
        return [rate_info]

    if rate_info is None:
        return [DEFAULT_SAMPLERATE]

    default = rate_info.default
    min_rate = rate_info.min
    max_rate = rate_info.max

    rates = []
    if isinstance(default, int):
        rates.append(default)

    if isinstance(min_rate, int):
        rates.append(min_rate)

    if isinstance(max_rate, int):
        rates.append(max_rate)

    if isinstance(min_rate, int) and isinstance(max_rate, int):
        rates.extend(
            r for r in DEFAULT_SAMPLERATE_CHOICES if min_rate <= r <= max_rate
        )

    return rates


def _extract_channels(format_field: EnumFormatItem) -> int:
    channels_info = format_field.channels

    if isinstance(channels_info, int):
        return channels_info

    if channels_info is None:
        return 1

    default = channels_info.default
    max_channels = channels_info.max

    if isinstance(max_channels, int):
        return max_channels

    return default


def _parse_pw_info(pw_info: dict) -> DeviceInfo:
    """Convert raw ``pw-dump`` node information into ``DeviceInfo``."""
    props = pw_info["props"]
    name = props["node.name"]
    description = props.get("node.description", name)

    adapter = TypeAdapter(list[EnumFormatItem])
    formats = adapter.validate_python(pw_info["params"]["EnumFormat"])

    default_format = formats[0]
    samplerates = set()
    for f in formats:
        samplerates.update(_extract_rate(f))

    return DeviceInfo(
        name=name,
        description=description,
        max_input_channels=_extract_channels(default_format),
        samplerates=list(samplerates),
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
