"""Main Textual config TUI application."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Static, Tree
from typing_extensions import get_origin

from .controller import ConfigEditorController
from .demo import ExampleProgramSettings
from .dialogs import MessageScreen
from .editors import (
    BaseEditor,
    CheckboxEditor,
    InputEditor,
    JsonEditor,
    SectionEditor,
    SelectEditor,
)
from .models import FieldNode, walk_schema
from .state import EditorSessionState
from .tree import ConfigTree
from .tree_presenter import TreePresenter
from .utils import (
    default_value,
    friendly_type_name,
    get_value,
    is_basemodel_type,
    json_safe,
)


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
        data = (
            value.model_dump(mode="json")
            if value is not None
            else self._build_initial_data(schema)
        )
        self.state = EditorSessionState(
            data=data,
            current_path=self.nodes[0].dotted_path if self.nodes else "",
        )
        self._tree_paths: dict[str, Any] = {}
        self.tree_presenter = TreePresenter(self)
        self.controller = ConfigEditorController(self, output_path=output_path)

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
        self.rebuild_tree()
        if self.state.current_path:
            self.load_node(self.node_lookup[self.state.current_path])

    def rebuild_tree(self) -> None:
        self.state.validation_errors = (
            self.controller.collect_validation_errors()
        )
        self.tree_presenter.rebuild()

    def focus_tree_at_current_path(self) -> None:
        tree = self.query_one("#config-tree", ConfigTree)
        if (
            self.state.current_path
            and self.state.current_path in self._tree_paths
        ):
            self.tree_presenter.expand_to_path(self.state.current_path)
            tree.select_node(self._tree_paths[self.state.current_path])
        tree.focus()

    def _set_editor_error(self, path: str, message: str) -> None:
        self.state.editor_errors[path] = message
        self.query_one("#editor-error", Static).update(message)

    def _clear_editor_error(self, path: str) -> None:
        self.state.editor_errors.pop(path, None)
        self.query_one("#editor-error", Static).update("")

    def _refresh_tree_node_label(self, node: FieldNode) -> None:
        self.tree_presenter.refresh_node_label(node)

    def _finish_successful_change(
        self, node: FieldNode, validated: BaseModel
    ) -> None:
        self.state.data = validated.model_dump(mode="json")
        self.controller.persist_validated_data(validated)
        self._clear_editor_error(node.dotted_path)
        self.state.validation_errors = {}
        self.rebuild_tree()
        self.load_node(node)
        self.focus_tree_at_current_path()

    def activate_tree_node(self) -> None:
        self.controller.activate_tree_node()

    def cancel_current_edit(self) -> None:
        self.controller.cancel_current_edit()

    def apply_current_edit(self) -> None:
        self.controller.apply_current_edit()

    @on(Tree.NodeSelected, "#config-tree")
    def handle_tree_selection(self, event: Tree.NodeSelected[Any]) -> None:
        dotted_path = event.node.data
        if (
            not isinstance(dotted_path, str)
            or dotted_path not in self.node_lookup
        ):
            return
        self.load_node(self.node_lookup[dotted_path])

    @on(Tree.NodeHighlighted, "#config-tree")
    def handle_tree_highlight(self, event: Tree.NodeHighlighted[Any]) -> None:
        dotted_path = event.node.data
        if (
            not isinstance(dotted_path, str)
            or dotted_path not in self.node_lookup
        ):
            return
        self.load_node(self.node_lookup[dotted_path])

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

    def load_node(self, node: FieldNode) -> None:
        self.state.current_path = node.dotted_path
        self.query_one("#editor-title", Static).update(node.title)
        self.query_one("#editor-help", Static).update(
            node.description or "No additional guidance for this setting.",
        )
        required = "Required" if node.required else "Optional"
        self.query_one("#editor-meta", Static).update(
            f"{required} | {friendly_type_name(node.effective_annotation)} | {node.dotted_path}",
        )
        self.query_one("#editor-error", Static).update(
            self.state.editor_errors.get(
                node.dotted_path,
                self.state.validation_errors.get(node.dotted_path, ""),
            ),
        )

        host = self.query_one("#editor-widget-host", Container)
        host.remove_children()
        editor = self._make_editor(node, get_value(self.state.data, node.path))
        host.mount(editor)

    def current_editor(self) -> BaseEditor:
        editor = self.query_one("#editor-widget-host > *")
        if not isinstance(editor, BaseEditor):
            raise RuntimeError(
                "Editor widget host does not contain a valid editor."
            )
        return editor

    def focus_current_editor_input(self) -> None:
        self.current_editor().focus_input()

    def apply_current_field(self, refocus_on_error: bool = False) -> None:
        self.controller.apply_current_field(refocus_on_error=refocus_on_error)

    @on(Button.Pressed, "#apply-value")
    def apply_value(self) -> None:
        self.apply_current_field(refocus_on_error=True)

    @on(Button.Pressed, "#reset-value")
    def reset_value(self) -> None:
        self.action_reset_field()

    def action_reset_field(self) -> None:
        self.controller.reset_field()

    def action_save(self) -> None:
        self.controller.finish()

    def action_export_json(self) -> None:
        self.controller.export_json()


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
