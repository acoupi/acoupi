"""Textual TUI for editing Pydantic configuration models.

This module is intentionally standalone so it can be explored without wiring it
into the rest of the Acoupi CLI yet.
"""

from __future__ import annotations

import datetime as dt
import json
import types
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, ValidationError
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
)
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Select,
    Static,
    TextArea,
    Tree,
)
from typing_extensions import Annotated, get_args, get_origin


def _titleize(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _split_annotated(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    if get_origin(annotation) == Annotated:
        args = get_args(annotation)
        return args[0], tuple(args[1:])
    return annotation, ()


def _is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    return origin in (Union, types.UnionType) and type(None) in get_args(
        annotation
    )


def _strip_optional(annotation: Any) -> Any:
    if not _is_optional(annotation):
        return annotation
    args = tuple(arg for arg in get_args(annotation) if arg is not type(None))
    if len(args) == 1:
        return args[0]
    return Union[args]


def _unwrap_annotation(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    base, metadata = _split_annotated(annotation)
    base = _strip_optional(base)
    nested_base, nested_metadata = _split_annotated(base)
    return nested_base, metadata + nested_metadata


def _is_basemodel_type(annotation: Any) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(
            annotation, BaseModel
        )
    except TypeError:
        return False


def _default_value(field: Any) -> Any:
    if field.default_factory is not None:
        return field.get_default(call_default_factory=True)
    if getattr(field, "default", None) is not None:
        return field.default
    return None


class BaseEditor(Container):
    """Base class for field editor widgets."""

    BINDINGS = [
        Binding("escape", "cancel_edit", "Cancel", show=False),
        Binding("ctrl+s", "apply_edit", "Apply", show=False),
        Binding("ctrl+r", "reset_edit", "Reset", show=False),
    ]

    def __init__(self, node: "FieldNode", value: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.node = node
        self.value = value

    def get_raw_value(self) -> Any:
        """Return the raw widget value."""
        raise NotImplementedError

    def focus_input(self) -> None:
        """Move keyboard focus to the main interactive control."""
        self.focus()

    def action_cancel_edit(self) -> None:
        app = self.app
        if not isinstance(app, ConfigEditorApp):
            return
        app.cancel_current_edit()

    def action_apply_edit(self) -> None:
        app = self.app
        if not isinstance(app, ConfigEditorApp):
            return
        app.apply_current_edit()

    def action_reset_edit(self) -> None:
        app = self.app
        if not isinstance(app, ConfigEditorApp):
            return
        app.action_reset_field()


FieldEditorType = type[BaseEditor]


class InputEditor(BaseEditor):
    """Single line text editor."""

    BINDINGS = [Binding("ctrl+s", "apply_edit", "Apply", show=False)]

    def compose(self) -> ComposeResult:
        yield Input(value=_to_display_value(self.value), id="editor-input")

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
        yield TextArea(_to_display_value(self.value), id="editor-json")
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
        children: list[FieldNode] = []
        if isinstance(app, ConfigEditorApp):
            children = app.get_child_nodes(self.node)

        yield Static(
            "This section contains the following settings.",
            classes="hint",
        )
        if not children:
            yield Static("No fields in this section.", classes="hint")
            return

        for child in children:
            value = None
            if isinstance(app, ConfigEditorApp):
                value = _get_value(app.data, child.path)
            yield Static(
                f"{child.title} ({_friendly_type_name(child.effective_annotation)}): {_summarize_value(value)}",
            )

    def get_raw_value(self) -> Any:
        return self.value


class ConfigTree(Tree[str]):
    """Tree widget that can hand focus to a selected leaf editor."""

    BINDINGS = [
        Binding("enter", "activate_current", "Activate", show=False),
        Binding("right", "activate_current", "Activate", show=False),
        Binding("left", "collapse_current", "Collapse", show=False),
        Binding("l", "activate_current", "Activate", show=False),
        Binding("h", "collapse_current", "Collapse", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def action_activate_current(self) -> None:
        app = self.app
        if not isinstance(app, ConfigEditorApp):
            return
        app.activate_tree_node()

    def action_collapse_current(self) -> None:
        node = self.cursor_node
        if node is None or not node.allow_expand:
            return
        if node.is_expanded:
            node.collapse()


@dataclass(frozen=True)
class FieldNode:
    """Description of a field in the configuration tree."""

    path: tuple[str, ...]
    field_name: str
    title: str
    annotation: Any
    field_info: Any
    parent_model: type[BaseModel]
    metadata: tuple[Any, ...]
    editor_factory: FieldEditorType | None

    @property
    def dotted_path(self) -> str:
        return ".".join(self.path)

    @property
    def description(self) -> str:
        return self.field_info.description or ""

    @property
    def required(self) -> bool:
        return self.field_info.is_required()

    @property
    def effective_annotation(self) -> Any:
        annotation, _ = _unwrap_annotation(self.annotation)
        return annotation

    @property
    def is_section(self) -> bool:
        return _is_basemodel_type(self.effective_annotation)

    @property
    def enum_type(self) -> type[Enum] | None:
        annotation = self.effective_annotation
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return annotation
        return None


def _extract_editor_factory(
    metadata: tuple[Any, ...],
) -> FieldEditorType | None:
    for item in metadata:
        if isinstance(item, type) and issubclass(item, BaseEditor):
            return item
    return None


def _walk_schema(
    schema: type[BaseModel],
    prefix: tuple[str, ...] = (),
) -> list[FieldNode]:
    nodes: list[FieldNode] = []
    for field_name, field in schema.model_fields.items():
        annotation = field.annotation
        if annotation is None:
            continue

        _, metadata = _unwrap_annotation(annotation)
        node = FieldNode(
            path=prefix + (field_name,),
            field_name=field_name,
            title=field.title or _titleize(field_name),
            annotation=annotation,
            field_info=field,
            parent_model=schema,
            metadata=metadata,
            editor_factory=_extract_editor_factory(metadata),
        )
        nodes.append(node)

        if node.is_section:
            nodes.extend(
                _walk_schema(node.effective_annotation, prefix=node.path)
            )
    return nodes


def _get_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _set_value(
    data: dict[str, Any], path: tuple[str, ...], value: Any
) -> None:
    current = data
    for part in path[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    if value is None:
        current.pop(path[-1], None)
    else:
        current[path[-1]] = value


def _coerce_scalar(annotation: Any, raw: str) -> Any:
    if annotation is str:
        return raw
    if annotation is int:
        return int(raw)
    if annotation is float:
        return float(raw)
    if annotation is bool:
        lower = raw.strip().lower()
        if lower in {"true", "t", "yes", "y", "1", "on"}:
            return True
        if lower in {"false", "f", "no", "n", "0", "off"}:
            return False
        raise ValueError("Enter yes/no or true/false.")
    if annotation is Path:
        return Path(raw).expanduser()
    if annotation is dt.time:
        return dt.time.fromisoformat(raw)
    if annotation is dt.date:
        return dt.date.fromisoformat(raw)
    if annotation is dt.datetime:
        return dt.datetime.fromisoformat(raw)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        for option in annotation:
            if raw == option.name or raw == str(option.value):
                return option
        raise ValueError("Choose one of the listed options.")
    return raw


def _coerce_value(node: FieldNode, raw: Any) -> Any:
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
        return _coerce_scalar(annotation, raw.strip())

    return raw


def _to_display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, BaseModel):
        return json.dumps(value.model_dump(mode="json"), indent=2)
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, indent=2, default=str)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, (dt.date, dt.time, dt.datetime)):
        return value.isoformat()
    return str(value)


def _friendly_type_name(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is list:
        return "List"
    if origin is dict:
        return "Object"
    if origin is tuple:
        return "List"
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return "Choice"
    if annotation is Path:
        return "Path"
    if annotation is dt.time:
        return "Time"
    if annotation is dt.date:
        return "Date"
    if annotation is dt.datetime:
        return "Date and time"
    if annotation is bool:
        return "On or off"
    if annotation is int:
        return "Whole number"
    if annotation is float:
        return "Number"
    if annotation is str:
        return "Text"
    if _is_basemodel_type(annotation):
        return "Section"
    return getattr(annotation, "__name__", "Value")


def _summarize_value(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, dict):
        return f"{len(value)} items"
    if isinstance(value, list):
        return f"{len(value)} items"
    text = _to_display_value(value).replace("\n", " ")
    return text[:28] + ("..." if len(text) > 28 else "")


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
        self.nodes = _walk_schema(schema)
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

    def _build_initial_data(self, schema: type[BaseModel]) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field_name, field in schema.model_fields.items():
            annotation, _ = _unwrap_annotation(field.annotation)
            default = _default_value(field)
            if default is not None:
                if isinstance(default, BaseModel):
                    data[field_name] = default.model_dump(mode="json")
                else:
                    data[field_name] = _json_safe(default)
            elif _is_basemodel_type(annotation):
                data[field_name] = self._build_initial_data(annotation)
        return data

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
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
            errors: dict[str, str] = {}
            for item in error.errors():
                location = item.get("loc", ())
                if not location:
                    continue
                path = ".".join(str(part) for part in location)
                errors[path] = item.get("msg", "Invalid value")
            return errors

    def _branch_has_error(self, path: tuple[str, ...]) -> bool:
        prefix = ".".join(path)
        return any(
            error == prefix or error.startswith(f"{prefix}.")
            for error in self.validation_errors
        )

    def _format_tree_label(self, node: FieldNode) -> str:
        if node.is_section:
            marker = (
                "[red]![/red]"
                if self._branch_has_error(node.path)
                else "[cyan]+[/cyan]"
            )
            return f"{marker} {node.title}"

        value = _get_value(self.data, node.path)
        if node.dotted_path in self.editor_errors or self._branch_has_error(
            node.path
        ):
            indicator = "[red]![/red]"
        elif value is None and node.required:
            indicator = "[yellow]?[/yellow]"
        else:
            indicator = "[green]•[/green]"
        return f"{indicator} {node.title}: {_summarize_value(value)}"

    def _rebuild_tree(self) -> None:
        self.validation_errors = self._collect_validation_errors()
        tree = self.query_one("#config-tree", Tree)
        tree.clear()
        tree.root.label = "Configuration"
        tree.root.expand()
        self._tree_paths = {}

        branch_index: dict[tuple[str, ...], Any] = {(): tree.root}
        for node in self.nodes:
            parent = branch_index[node.path[:-1]]
            branch = parent.add(
                self._format_tree_label(node),
                data=node.dotted_path,
            )
            self._tree_paths[node.dotted_path] = branch
            if node.is_section:
                branch.allow_expand = True
                branch.collapse()
                branch_index[node.path] = branch
            else:
                branch.allow_expand = False

        if self.current_path and self.current_path in self._tree_paths:
            self._expand_to_path(self.current_path)
            tree.select_node(self._tree_paths[self.current_path])

    def _expand_to_path(self, dotted_path: str) -> None:
        parts = dotted_path.split(".")
        for size in range(1, len(parts)):
            prefix = ".".join(parts[:size])
            branch = self._tree_paths.get(prefix)
            if branch is not None:
                branch.expand()

    def _focus_tree_at_current_path(self) -> None:
        tree = self.query_one("#config-tree", ConfigTree)
        if self.current_path and self.current_path in self._tree_paths:
            self._expand_to_path(self.current_path)
            tree.select_node(self._tree_paths[self.current_path])
        tree.focus()

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
        if not self.current_path:
            return
        node = self.node_lookup[self.current_path]
        self.query_one("#editor-error", Static).update("")
        self.editor_errors.pop(node.dotted_path, None)
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
        if factory is not None:
            return factory(node, value)

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
            f"{required} | {_friendly_type_name(node.effective_annotation)} | {node.dotted_path}",
        )
        self.query_one("#editor-error", Static).update(
            self.editor_errors.get(
                node.dotted_path,
                self.validation_errors.get(node.dotted_path, ""),
            ),
        )

        host = self.query_one("#editor-widget-host", Container)
        host.remove_children()
        editor = self._make_editor(node, _get_value(self.data, node.path))
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

    def _is_editor_control_focused(self) -> bool:
        focused = self.focused
        if focused is None:
            return False
        if isinstance(focused, (Input, Checkbox, Select, TextArea)):
            return True
        return False

    def _validate_data(self) -> BaseModel:
        return self.schema.model_validate(self.data)

    def _candidate_validation_errors(
        self,
        path: tuple[str, ...],
        value: Any,
    ) -> dict[str, str]:
        candidate = dict(self.data)
        _set_value(candidate, path, value)
        try:
            self.schema.model_validate(candidate)
        except ValidationError as error:
            errors: dict[str, str] = {}
            for item in error.errors():
                location = item.get("loc", ())
                if not location:
                    continue
                dotted = ".".join(str(part) for part in location)
                errors[dotted] = item.get("msg", "Invalid value")
            return errors
        return {}

    def _persist_validated_data(self, validated: BaseModel) -> None:
        if self.output_path is None:
            return
        if not self.output_path.parent.exists():
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(validated.model_dump_json(indent=2))

    def _apply_current_field(self, refocus_on_error: bool = False) -> None:
        if not self.current_path:
            return
        node = self.node_lookup[self.current_path]
        raw = self._current_editor().get_raw_value()
        try:
            value = _coerce_value(node, raw)
        except (ValueError, json.JSONDecodeError) as error:
            self.editor_errors[node.dotted_path] = str(error)
            self.query_one("#editor-error", Static).update(str(error))
            self.validation_errors = {}
            tree_node = self._tree_paths.get(node.dotted_path)
            if tree_node is not None:
                tree_node.set_label(self._format_tree_label(node))
            if refocus_on_error:
                self._focus_current_editor_input()
            return

        candidate_errors = self._candidate_validation_errors(node.path, value)
        if candidate_errors:
            self.editor_errors[node.dotted_path] = candidate_errors.get(
                node.dotted_path,
                "This value is not valid.",
            )
            self.query_one("#editor-error", Static).update(
                self.editor_errors[node.dotted_path],
            )
            self.validation_errors = candidate_errors
            tree_node = self._tree_paths.get(node.dotted_path)
            if tree_node is not None:
                tree_node.set_label(self._format_tree_label(node))
            if refocus_on_error:
                self._focus_current_editor_input()
            return

        self.editor_errors.pop(node.dotted_path, None)
        _set_value(self.data, node.path, value)
        validated = self._validate_data()

        self.data = validated.model_dump(mode="json")
        self._persist_validated_data(validated)
        self.query_one("#editor-error", Static).update("")
        self.validation_errors = {}
        self._rebuild_tree()
        self._load_node(node)
        self._focus_tree_at_current_path()

    @on(Button.Pressed, "#apply-value")
    def apply_value(self) -> None:
        self._apply_current_field(refocus_on_error=True)

    @on(Button.Pressed, "#reset-value")
    def reset_value(self) -> None:
        self.action_reset_field()

    def action_reset_field(self) -> None:
        if not self.current_path:
            return
        node = self.node_lookup[self.current_path]
        default = _default_value(node.field_info)
        if isinstance(default, BaseModel):
            default = default.model_dump(mode="json")
        elif default is not None:
            default = _json_safe(default)
        self.editor_errors.pop(node.dotted_path, None)
        _set_value(self.data, node.path, default)
        try:
            validated = self._validate_data()
        except ValidationError:
            self.validation_errors = self._collect_validation_errors()
        else:
            self.data = validated.model_dump(mode="json")
            self._persist_validated_data(validated)
            self.validation_errors = {}
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
        yield Input(value=_to_display_value(self.value), id="editor-input")


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


if __name__ == "__main__":
    main()
