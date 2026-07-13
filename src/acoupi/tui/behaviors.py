"""Runtime field behaviors for the Textual config TUI.

These hooks keep dynamic field logic out of the widgets. The controller asks a
behavior for state-dependent choices or extra validation before falling back to
plain schema-driven handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class ChoiceOption:
    """A user-facing option for a constrained field."""

    value: Any
    label: str


@dataclass(frozen=True)
class FieldBehaviorContext:
    """Runtime context made available to field behaviors."""

    schema: type[BaseModel]
    data: dict[str, Any]
    node: Any


class FieldBehavior:
    """Optional dynamic behavior for a field."""

    def get_options(
        self,
        context: FieldBehaviorContext,
    ) -> list[ChoiceOption] | None:
        return None

    def validate(
        self,
        value: Any,
        context: FieldBehaviorContext,
    ) -> str | None:
        return None


def extract_field_behavior(metadata: tuple[Any, ...]) -> FieldBehavior | None:
    """Extract the first behavior object attached via field metadata.

    This keeps the core generic: schemas opt into runtime behavior explicitly
    instead of the TUI hard-coding knowledge about particular config classes.
    """
    for item in metadata:
        if isinstance(item, FieldBehavior):
            return item
    return None
