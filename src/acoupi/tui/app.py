"""Main Textual config TUI application."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Static, Tree
from typing_extensions import Annotated, get_origin

from .editors import (
    BaseEditor,
    CheckboxEditor,
    InputEditor,
    JsonEditor,
    SectionEditor,
    SelectEditor,
)
from .models import FieldNode, walk_schema
from .tree import ConfigTree
from .tree_presenter import TreePresenter
from .utils import (
    coerce_scalar,
    default_value,
    friendly_type_name,
    get_value,
    is_basemodel_type,
    json_safe,
    set_value,
    summarize_value,
    to_display_value,
    validation_errors_by_path,
)


def coerce_value(node: FieldNode, raw: Any) -> Any:
    annotation = node.effective_annotation
    origin = get_origin(annotation)

    if raw is None:
        return None

    if isinstance(raw, str) and not raw.strip() and not node.required:
        return None

    if node.is_section:
        if isinstance(raw, dict):
            return raw
        raise ValueError("Nested sections are edited from the tree.")

    if origin in (list, dict, tuple):
        if isinstance(raw, str):
            return json.loads(raw)
        return raw

    if isinstance(raw, bool):
        return raw

    if isinstance(raw, str):
        return coerce_scalar(annotation, raw.strip())

    return raw


class MessageScreen(ModalScreen[None]):
    """Simple modal for messages."""

    CSS = """
    MessageScreen {
        align: center middle;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="message-modal"):
            yield Static(self._title, classes="modal-title")
            yield Static(self._message, classes="modal-body")
            yield Button("Close", id="close-message", variant="primary")

    @on(Button.Pressed, "#close-message")
    def close(self) -> None:
        self.dismiss(None)


class ConfigEditorApp(App[Optional[BaseModel]]):
    """Interactive editor for Pydantic configuration models."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #tree-pane {
        width: 54;
        border: round $surface;
        padding: 1;
    }

    #editor-pane {
        border: round $surface;
        padding: 1;
    }

    #tree-pane:focus-within {
        border: round $primary;
    }

    #editor-pane {
        width: 1fr;
    }

    #config-tree {
        height: 1fr;
    }

    #editor-widget-host {
        min-height: 8;
    }

    #editor-widget-host:can-focus {
        display: none;
    }

    #editor-json {
        height: 12;
    }

    .hint {
        color: $text-muted;
    }

    .section-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #editor-error {
        color: $error;
        margin-bottom: 1;
        min-height: 3;
    }

    #message-modal {
        width: 72;
        height: auto;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }

    .modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .modal-body {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "apply_current_edit", "Apply", priority=True),
        Binding("ctrl+e", "export_json", "Export"),
        Binding("ctrl+r", "reset_field", "Reset field"),
        Binding("ctrl+x", "save", "Finish", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        schema: type[BaseModel],
        value: Optional[BaseModel] = None,
        output_path: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self.schema = schema
        self.output_path = output_path
        self.nodes = walk_schema(schema)
        self.node_lookup = {node.dotted_path: node for node in self.nodes}
        self.data = (
            value.model_dump(mode="json")
            if value is not None
            else self._build_initial_data(schema)
        )
        self.validation_errors: dict[str, str] = {}
        self.editor_errors: dict[str, str] = {}
        self.current_path = self.nodes[0].dotted_path if self.nodes else ""
        self._tree_paths: dict[str, Any] = {}
        self.tree_presenter = TreePresenter(self)

    def _build_initial_data(self, schema: type[BaseModel]) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field_name, field in schema.model_fields.items():
            annotation = field.annotation
            default = default_value(field)
            if default is not None:
                if isinstance(default, BaseModel):
                    data[field_name] = default.model_dump(mode="json")
                else:
                    data[field_name] = json_safe(default)
            elif annotation is not None and is_basemodel_type(annotation):
                data[field_name] = self._build_initial_data(annotation)
        return data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="tree-pane"):
                yield Static("Configuration", classes="section-title")
                yield ConfigTree("Configuration", id="config-tree")
            with Vertical(id="editor-pane"):
                yield Static(
                    "Details", id="editor-title", classes="section-title"
                )
                yield Static("Select a setting to edit.", id="editor-help")
                yield Static("", id="editor-meta", classes="hint")
                yield Static("", id="editor-error")
                yield Container(id="editor-widget-host")
                with Horizontal():
                    yield Button("Apply", id="apply-value", variant="primary")
                    yield Button("Reset to default", id="reset-value")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#editor-widget-host", Container).can_focus = False
        self._rebuild_tree()
        if self.current_path:
            self._load_node(self.node_lookup[self.current_path])

    def _collect_validation_errors(self) -> dict[str, str]:
        try:
            self.schema.model_validate(self.data)
            return {}
        except ValidationError as error:
            return validation_errors_by_path(error)

    def _rebuild_tree(self) -> None:
        self.validation_errors = self._collect_validation_errors()
        self.tree_presenter.rebuild()

    def _focus_tree_at_current_path(self) -> None:
        tree = self.query_one("#config-tree", ConfigTree)
        if self.current_path and self.current_path in self._tree_paths:
            self.tree_presenter.expand_to_path(self.current_path)
            tree.select_node(self._tree_paths[self.current_path])
        tree.focus()

    def _get_current_node(self) -> FieldNode | None:
        if not self.current_path:
            return None
        return self.node_lookup[self.current_path]

    def _set_editor_error(self, path: str, message: str) -> None:
        self.editor_errors[path] = message
        self.query_one("#editor-error", Static).update(message)

    def _clear_editor_error(self, path: str) -> None:
        self.editor_errors.pop(path, None)
        self.query_one("#editor-error", Static).update("")

    def _refresh_tree_node_label(self, node: FieldNode) -> None:
        self.tree_presenter.refresh_node_label(node)

    def _finish_successful_change(
        self, node: FieldNode, validated: BaseModel
    ) -> None:
        self.data = validated.model_dump(mode="json")
        self._persist_validated_data(validated)
        self._clear_editor_error(node.dotted_path)
        self.validation_errors = {}
        self._rebuild_tree()
        self._load_node(node)
        self._focus_tree_at_current_path()

    def activate_tree_node(self) -> None:
        tree = self.query_one("#config-tree", ConfigTree)
        cursor_node = tree.cursor_node
        if cursor_node is None:
            return

        dotted_path = cursor_node.data
        if not isinstance(dotted_path, str):
            return

        node = self.node_lookup.get(dotted_path)
        if node is None:
            return

        self._load_node(node)

        if node.is_section:
            if not cursor_node.is_expanded:
                cursor_node.expand()
            return

        self.call_after_refresh(self._focus_current_editor_input)

    def cancel_current_edit(self) -> None:
        node = self._get_current_node()
        if node is None:
            return
        self._clear_editor_error(node.dotted_path)
        self._load_node(node)
        self._focus_tree_at_current_path()

    def apply_current_edit(self) -> None:
        self._apply_current_field(refocus_on_error=True)

    @on(Tree.NodeSelected, "#config-tree")
    def handle_tree_selection(self, event: Tree.NodeSelected[Any]) -> None:
        dotted_path = event.node.data
        if (
            not isinstance(dotted_path, str)
            or dotted_path not in self.node_lookup
        ):
            return
        self._load_node(self.node_lookup[dotted_path])

    @on(Tree.NodeHighlighted, "#config-tree")
    def handle_tree_highlight(self, event: Tree.NodeHighlighted[Any]) -> None:
        dotted_path = event.node.data
        if (
            not isinstance(dotted_path, str)
            or dotted_path not in self.node_lookup
        ):
            return
        self._load_node(self.node_lookup[dotted_path])

    def get_child_nodes(self, node: FieldNode) -> list[FieldNode]:
        depth = len(node.path) + 1
        return [
            child
            for child in self.nodes
            if len(child.path) == depth and child.path[:-1] == node.path
        ]

    def _make_editor(self, node: FieldNode, value: Any) -> BaseEditor:
        factory = node.editor_factory
        if (
            factory is not None
            and isinstance(factory, type)
            and issubclass(factory, BaseEditor)
        ):
            return factory(node, value)

        return self._make_default_editor(node, value)

    def _make_default_editor(self, node: FieldNode, value: Any) -> BaseEditor:
        annotation = node.effective_annotation
        origin = get_origin(annotation)
        if node.is_section:
            return SectionEditor(node, value)
        if node.enum_type is not None:
            return SelectEditor(node, value)
        if annotation is bool:
            return CheckboxEditor(node, value)
        if origin in (list, dict, tuple):
            return JsonEditor(node, value)
        return InputEditor(node, value)

    def _load_node(self, node: FieldNode) -> None:
        self.current_path = node.dotted_path
        self.query_one("#editor-title", Static).update(node.title)
        self.query_one("#editor-help", Static).update(
            node.description or "No additional guidance for this setting.",
        )
        required = "Required" if node.required else "Optional"
        self.query_one("#editor-meta", Static).update(
            f"{required} | {friendly_type_name(node.effective_annotation)} | {node.dotted_path}",
        )
        self.query_one("#editor-error", Static).update(
            self.editor_errors.get(
                node.dotted_path,
                self.validation_errors.get(node.dotted_path, ""),
            ),
        )

        host = self.query_one("#editor-widget-host", Container)
        host.remove_children()
        editor = self._make_editor(node, get_value(self.data, node.path))
        host.mount(editor)

    def _current_editor(self) -> BaseEditor:
        editor = self.query_one("#editor-widget-host > *")
        if not isinstance(editor, BaseEditor):
            raise RuntimeError(
                "Editor widget host does not contain a valid editor."
            )
        return editor

    def _focus_current_editor_input(self) -> None:
        self._current_editor().focus_input()

    def _validate_data(self) -> BaseModel:
        return self.schema.model_validate(self.data)

    def _candidate_validation_errors(
        self,
        path: tuple[str, ...],
        value: Any,
    ) -> dict[str, str]:
        candidate = dict(self.data)
        set_value(candidate, path, value)
        try:
            self.schema.model_validate(candidate)
        except ValidationError as error:
            return validation_errors_by_path(error)
        return {}

    def _persist_validated_data(self, validated: BaseModel) -> None:
        if self.output_path is None:
            return
        if not self.output_path.parent.exists():
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(validated.model_dump_json(indent=2))

    def _apply_current_field(self, refocus_on_error: bool = False) -> None:
        node = self._get_current_node()
        if node is None:
            return
        raw = self._current_editor().get_raw_value()
        try:
            value = coerce_value(node, raw)
        except (ValueError, json.JSONDecodeError) as error:
            self._set_editor_error(node.dotted_path, str(error))
            self.validation_errors = {}
            self._refresh_tree_node_label(node)
            if refocus_on_error:
                self._focus_current_editor_input()
            return

        candidate_errors = self._candidate_validation_errors(node.path, value)
        if candidate_errors:
            self._set_editor_error(
                node.dotted_path,
                candidate_errors.get(
                    node.dotted_path,
                    "This value is not valid.",
                ),
            )
            self.validation_errors = candidate_errors
            self._refresh_tree_node_label(node)
            if refocus_on_error:
                self._focus_current_editor_input()
            return

        set_value(self.data, node.path, value)
        validated = self._validate_data()
        self._finish_successful_change(node, validated)

    @on(Button.Pressed, "#apply-value")
    def apply_value(self) -> None:
        self._apply_current_field(refocus_on_error=True)

    @on(Button.Pressed, "#reset-value")
    def reset_value(self) -> None:
        self.action_reset_field()

    def action_reset_field(self) -> None:
        node = self._get_current_node()
        if node is None:
            return
        default = default_value(node.field_info)
        if isinstance(default, BaseModel):
            default = default.model_dump(mode="json")
        elif default is not None:
            default = json_safe(default)
        self._clear_editor_error(node.dotted_path)
        set_value(self.data, node.path, default)
        try:
            validated = self._validate_data()
        except ValidationError:
            self.validation_errors = self._collect_validation_errors()
        else:
            self._finish_successful_change(node, validated)
            return
        self._rebuild_tree()
        self._load_node(node)
        self._focus_tree_at_current_path()

    def action_save(self) -> None:
        try:
            validated = self._validate_data()
        except ValidationError as error:
            self.push_screen(MessageScreen("Cannot save", str(error)))
            return
        self.exit(validated)

    def action_export_json(self) -> None:
        try:
            validated = self._validate_data()
        except ValidationError as error:
            self.push_screen(MessageScreen("Cannot export", str(error)))
            return
        self.push_screen(
            MessageScreen(
                "Current configuration", validated.model_dump_json(indent=2)
            ),
        )


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


def run_editor(
    schema: type[BaseModel],
    value: Optional[BaseModel] = None,
    output_path: Optional[Path] = None,
) -> Optional[BaseModel]:
    """Run the configuration editor for a schema."""
    return ConfigEditorApp(
        schema=schema,
        value=value,
        output_path=output_path,
    ).run()


def main() -> None:
    """Launch a demo editor when run as a module."""
    result = run_editor(ExampleProgramSettings)
    if result is not None:
        print(result.model_dump_json(indent=2))
