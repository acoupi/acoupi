"""State objects for the Textual config TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EditorSessionState:
    """Mutable session state for the config editor."""

    data: dict[str, Any]
    current_path: str = ""
    validation_errors: dict[str, str] = field(default_factory=dict)
    editor_errors: dict[str, str] = field(default_factory=dict)
