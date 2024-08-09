"""Program templates.

This module provides functions that facilitate the creation of programs.
"""

import datetime
from pathlib import Path
from typing import Annotated, List, Optional, Type

from pydantic import BaseModel, Field

from acoupi.components import types
from acoupi.data import TimeInterval
from acoupi.programs.base import AcoupiProgram, NoUserPrompt

__all__ = [
    "create_base_program",
]


class AudioConfiguration(BaseModel):
    duration: int = 3
    """Duration of each audio recording in seconds."""

    interval: int = 5
    """Interval between each audio recording in seconds."""

    chunksize: Annotated[int, NoUserPrompt] = 8192
    """Chunksize of audio recording."""

    schedule: List[TimeInterval] = Field(
        default_factory=lambda: [
            TimeInterval(start=datetime.time.min, end=datetime.time.max)
        ]
    )


class FileConfiguration(BaseModel):
    audio_directory: Path = Field(
        default_factory=lambda: Path.home() / "audio"
    )
    """Directory to save audio recordings."""


class StorageConfiguration(BaseModel):
    metadata_db: Path = Field(
        default_factory=lambda: Path.home() / "metadata.db"
    )

    messages_db: Path = Field(
        default_factory=lambda: Path.home() / "messages.db"
    )


def create_base_program(
    models: Optional[List[Type[types.Model]]] = None,
    messenger: Optional[Type[types.Messenger]] = None,
    summarizers: Optional[List[Type[types.Summariser]]] = None,
    config_schema: Optional[Type[BaseModel]] = None,
) -> Type[AcoupiProgram]:
    class Program(AcoupiProgram):
        config: config_schema

    # Recording
    # - Recording Schedule: Frequency
    # - Recording Conditions: Interval type
    # Model processing
    # File management
    # Messages
    # Summary
    # Heartbeat

    return Program
