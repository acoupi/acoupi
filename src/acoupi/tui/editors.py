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


def _call_app_method(app: Any, name: str) -> None:
    handler = getattr(app, name, None)
    if callable(handler):
        handler()


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
        _call_app_method(self.app, "cancel_current_edit")

    def action_apply_edit(self) -> None:
        _call_app_method(self.app, "apply_current_edit")

    def action_reset_edit(self) -> None:
        _call_app_method(self.app, "action_reset_field")


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
        options: list[tuple[str, Any]] = []
        runtime_options = None
        app = self.app
        controller = getattr(app, "controller", None)
        runtime_getter = getattr(controller, "runtime_options", None)
        if callable(runtime_getter):
            maybe_options = runtime_getter(self.node)
            if isinstance(maybe_options, list):
                runtime_options = maybe_options

        if runtime_options:
            options = [
                (option.label, option.value) for option in runtime_options
            ]
        else:
            options = [
                (str(member.value), str(member.value))
                for member in self.node.enum_type or []
            ]

        current = self.value
        allowed_values = {option_value for _, option_value in options}

        # Textual Select rejects values that are not present in the option set.
        # Runtime-dependent fields often start unset, so we only pass an
        # explicit value when it is actually valid for the current option list.
        if current in allowed_values:
            yield Select(options=options, value=current, id="editor-select")
            return

        prompt = "Choose an option" if options else "No options available"
        yield Select(options=options, prompt=prompt, id="editor-select")

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
