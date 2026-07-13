"""Demo schemas and widgets for the Textual config TUI."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from textual.app import ComposeResult
from textual.widgets import Input, Static
from typing_extensions import Annotated

from acoupi.devices.audio.pipewire import get_input_devices

from .behaviors import ChoiceOption, FieldBehavior, FieldBehaviorContext
from .editors import InputEditor
from .utils import to_display_value


class TimeInputEditor(InputEditor):
    """Example custom editor for time values."""

    def compose(self) -> ComposeResult:
        yield Static(
            "Use 24-hour format, for example 06:30:00.", classes="hint"
        )
        yield Input(value=to_display_value(self.value), id="editor-input")


class PipeWireDeviceBehavior(FieldBehavior):
    """Expose live PipeWire devices as friendly choices in the demo."""

    def get_options(
        self,
        context: FieldBehaviorContext,
    ) -> list[ChoiceOption] | None:
        return [
            ChoiceOption(value=device.name, label=device.description)
            for device in get_input_devices()
        ]


class PipeWireSampleRateBehavior(FieldBehavior):
    """Samplerates depend on the selected PipeWire device."""

    def get_options(
        self,
        context: FieldBehaviorContext,
    ) -> list[ChoiceOption] | None:
        device_name = context.data.get("device_name")
        if not device_name:
            return None
        for device in get_input_devices():
            if device.name == device_name:
                return [
                    ChoiceOption(value=rate, label=f"{rate} Hz")
                    for rate in sorted(device.samplerates)
                ]
        return None

    def validate(
        self,
        value: Any,
        context: FieldBehaviorContext,
    ) -> str | None:
        options = self.get_options(context)
        if options is None:
            return "Select a device before choosing a samplerate."
        allowed = {option.value for option in options}
        if value not in allowed:
            return "Samplerate is not supported by the selected device."
        return None


class PipeWireChannelsBehavior(FieldBehavior):
    """Channel choices depend on the selected PipeWire device."""

    def get_options(
        self,
        context: FieldBehaviorContext,
    ) -> list[ChoiceOption] | None:
        device_name = context.data.get("device_name")
        if not device_name:
            return None
        for device in get_input_devices():
            if device.name == device_name:
                return [
                    ChoiceOption(value=channel, label=f"{channel} channels")
                    for channel in range(1, device.max_input_channels + 1)
                ]
        return None

    def validate(
        self,
        value: Any,
        context: FieldBehaviorContext,
    ) -> str | None:
        options = self.get_options(context)
        if options is None:
            return "Select a device before choosing the number of channels."
        allowed = {option.value for option in options}
        if value not in allowed:
            return "Channel count is not supported by the selected device."
        return None


class DemoPWRecorderConfig(BaseModel):
    """PipeWire recorder config with demo-specific runtime field behaviors."""

    device_name: Annotated[str, PipeWireDeviceBehavior()]
    samplerate: Annotated[int, PipeWireSampleRateBehavior()] = 48_000
    audio_channels: Annotated[int, PipeWireChannelsBehavior()] = 1
    time_expansion: float = Field(default=1, gt=0)


class ExampleAudioSettings(BaseModel):
    duration: int = Field(
        default=3, description="Length of each recording in seconds."
    )
    interval: int = Field(
        default=10, description="Time between recordings in seconds."
    )
    schedule_start: Annotated[
        dt.time,
        TimeInputEditor,
    ] = Field(
        default=dt.time(hour=6, minute=0),
        description="Time of day when recording should start.",
    )
    schedule_end: Annotated[
        dt.time,
        TimeInputEditor,
    ] = Field(
        default=dt.time(hour=22, minute=0),
        description="Time of day when recording should stop.",
    )


class ExampleStorageSettings(BaseModel):
    recordings_folder: Path = Field(
        default=Path.home() / "recordings",
        description="Folder where finished recordings are stored.",
    )
    metadata_file: Path = Field(
        default=Path.home() / "recordings" / "metadata.json",
        description="File used to keep recording details.",
    )


class ExampleProgramSettings(BaseModel):
    device_name: str = Field(
        default="field-recorder-01",
        description="A friendly name for this device.",
    )
    timezone: str = Field(
        default="Europe/London",
        description="Time zone used for schedules and timestamps.",
    )
    use_noise_filter: bool = Field(
        default=True,
        description="Reduce steady background noise before saving clips.",
    )
    tags: list[str] = Field(
        default_factory=lambda: ["demo", "bioacoustics"],
        description="Optional labels to help identify this setup.",
    )
    audio: ExampleAudioSettings = Field(
        default_factory=ExampleAudioSettings,
        description="Recording settings.",
    )
    storage: ExampleStorageSettings = Field(
        default_factory=ExampleStorageSettings,
        description="Where files should be stored.",
    )


class ExamplePipeWireProgramSettings(BaseModel):
    """Demo schema that exercises runtime-dependent PipeWire field behavior."""

    device_name: str = Field(
        default="pipewire-demo",
        description="A friendly name for this deployment.",
    )
    timezone: str = Field(
        default="Europe/London",
        description="Time zone used for schedules and timestamps.",
    )
    microphone: DemoPWRecorderConfig = Field(
        description=(
            "PipeWire recorder settings. Available samplerates and channel "
            "counts depend on the selected input device."
        ),
    )
    audio: ExampleAudioSettings = Field(
        default_factory=ExampleAudioSettings,
        description="Recording settings.",
    )
    storage: ExampleStorageSettings = Field(
        default_factory=ExampleStorageSettings,
        description="Where files should be stored.",
    )
