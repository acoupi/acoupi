"""Demo schemas and widgets for the Textual config TUI."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from pydantic import BaseModel, Field
from textual.app import ComposeResult
from textual.widgets import Input, Static
from typing_extensions import Annotated

from .editors import InputEditor
from .utils import to_display_value


class TimeInputEditor(InputEditor):
    """Example custom editor for time values."""

    def compose(self) -> ComposeResult:
        yield Static(
            "Use 24-hour format, for example 06:30:00.", classes="hint"
        )
        yield Input(value=to_display_value(self.value), id="editor-input")


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
