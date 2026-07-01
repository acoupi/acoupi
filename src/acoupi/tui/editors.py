"""Editor widgets for the Textual config TUI."""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Checkbox, Input, Select, Static, TextArea

from .utils import (
    friendly_type_name,
    get_value,
    summarize_value,
    to_display_value,
)


class BaseEditor(Container):
    """Base class for field editor widgets."""

    BINDINGS = [
        Binding("escape", "cancel_edit", "Cancel", show=False),
        Binding("ctrl+s", "apply_edit", "Apply", show=False),
        Binding("ctrl+r", "reset_edit", "Reset", show=False),
    ]

    def __init__(self, node: Any, value: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.node = node
        self.value = value

    def get_raw_value(self) -> Any:
        raise NotImplementedError

    def focus_input(self) -> None:
        self.focus()

    def action_cancel_edit(self) -> None:
        app = self.app
        handler = getattr(app, "cancel_current_edit", None)
        if callable(handler):
            handler()

    def action_apply_edit(self) -> None:
        app = self.app
        handler = getattr(app, "apply_current_edit", None)
        if callable(handler):
            handler()

    def action_reset_edit(self) -> None:
        app = self.app
        handler = getattr(app, "action_reset_field", None)
        if callable(handler):
            handler()


class InputEditor(BaseEditor):
    """Single line text editor."""

    BINDINGS = [Binding("ctrl+s", "apply_edit", "Apply", show=False)]

    def compose(self) -> ComposeResult:
        yield Input(value=to_display_value(self.value), id="editor-input")

    def get_raw_value(self) -> Any:
        return self.query_one("#editor-input", Input).value

    @on(Input.Submitted, "#editor-input")
    def submit_input(self) -> None:
        self.action_apply_edit()

    def focus_input(self) -> None:
        self.query_one("#editor-input", Input).focus()


class CheckboxEditor(BaseEditor):
    """Boolean editor."""

    BINDINGS = [Binding("ctrl+s", "apply_edit", "Apply", show=False)]

    def compose(self) -> ComposeResult:
        yield Checkbox("Enabled", value=bool(self.value), id="editor-checkbox")

    def get_raw_value(self) -> Any:
        return self.query_one("#editor-checkbox", Checkbox).value

    def focus_input(self) -> None:
        self.query_one("#editor-checkbox", Checkbox).focus()


class SelectEditor(BaseEditor):
    """Enum editor."""

    BINDINGS = [Binding("ctrl+s", "apply_edit", "Apply", show=False)]

    def compose(self) -> ComposeResult:
        options = [
            (str(member.value), str(member.value))
            for member in self.node.enum_type or []
        ]
        current = "" if self.value is None else str(self.value)
        yield Select(options=options, value=current, id="editor-select")

    def get_raw_value(self) -> Any:
        return self.query_one("#editor-select", Select).value

    def focus_input(self) -> None:
        self.query_one("#editor-select", Select).focus()


class JsonEditor(BaseEditor):
    """JSON editor for structured values."""

    BINDINGS = [Binding("ctrl+s", "apply_edit", "Apply", show=False)]

    def compose(self) -> ComposeResult:
        yield TextArea(to_display_value(self.value), id="editor-json")
        yield Static(
            "Use JSON for lists or structured values.",
            classes="hint",
        )

    def get_raw_value(self) -> Any:
        return self.query_one("#editor-json", TextArea).text

    def focus_input(self) -> None:
        self.query_one("#editor-json", TextArea).focus()


class SectionEditor(BaseEditor):
    """Read-only editor for nested sections."""

    def compose(self) -> ComposeResult:
        app = self.app
        children: list[Any] = []
        child_getter = getattr(app, "get_child_nodes", None)
        if callable(child_getter):
            maybe_children = child_getter(self.node)
            if isinstance(maybe_children, list):
                children = maybe_children

        yield Static(
            "This section contains the following settings.",
            classes="hint",
        )
        if not children:
            yield Static("No fields in this section.", classes="hint")
            return

        for child in children:
            value = None
            data = getattr(app, "data", None)
            if isinstance(data, dict):
                value = get_value(data, child.path)
            yield Static(
                f"{child.title} ({friendly_type_name(child.effective_annotation)}): {summarize_value(value)}",
            )

    def get_raw_value(self) -> Any:
        return self.value
