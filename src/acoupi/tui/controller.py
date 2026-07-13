"""Controller logic for the Textual config TUI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from textual.widgets import Static, Tree

from .behaviors import ChoiceOption, FieldBehaviorContext
from .dialogs import MessageScreen
from .models import FieldNode
from .utils import (
    coerce_scalar,
    default_value,
    get_value,
    json_safe,
    set_value,
    validation_errors_by_path,
)


def coerce_value(node: FieldNode, raw: Any) -> Any:
    annotation = node.effective_annotation
    origin = getattr(annotation, "__origin__", None)

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


class ConfigEditorController:
    """Coordinates view events with config state updates."""

    def __init__(self, app: Any, output_path: Path | None = None) -> None:
        self.app = app
        self.output_path = output_path

    @property
    def state(self):
        return self.app.state

    def current_node(self) -> FieldNode | None:
        if not self.state.current_path:
            return None
        return self.app.node_lookup[self.state.current_path]

    def field_context(self, node: FieldNode) -> FieldBehaviorContext:
        local_data = get_value(self.state.data, node.path[:-1])
        if not isinstance(local_data, dict):
            local_data = dict(self.state.data)
        return FieldBehaviorContext(
            schema=node.parent_model,
            data=dict(local_data),
            node=node,
        )

    def runtime_options(self, node: FieldNode) -> list[ChoiceOption] | None:
        if node.behavior is None:
            return None
        return node.behavior.get_options(self.field_context(node))

    def collect_validation_errors(self) -> dict[str, str]:
        try:
            self.app.schema.model_validate(self.state.data)
            return {}
        except ValidationError as error:
            return validation_errors_by_path(error)

    def validate_data(self) -> BaseModel:
        return self.app.schema.model_validate(self.state.data)

    def candidate_validation_errors(
        self,
        path: tuple[str, ...],
        value: Any,
    ) -> dict[str, str]:
        candidate = dict(self.state.data)
        set_value(candidate, path, value)
        try:
            self.app.schema.model_validate(candidate)
        except ValidationError as error:
            return validation_errors_by_path(error)
        return {}

    def runtime_validation_error(
        self,
        node: FieldNode,
        value: Any,
    ) -> str | None:
        if node.behavior is None:
            return None

        local_data = get_value(self.state.data, node.path[:-1])
        if not isinstance(local_data, dict):
            local_data = dict(self.state.data)
        data = dict(local_data)
        data[node.field_name] = value
        return node.behavior.validate(
            value,
            FieldBehaviorContext(
                schema=node.parent_model,
                data=data,
                node=node,
            ),
        )

    def persist_validated_data(self, validated: BaseModel) -> None:
        if self.output_path is None:
            return
        if not self.output_path.parent.exists():
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(validated.model_dump_json(indent=2))

    def set_editor_error(self, path: str, message: str) -> None:
        self.state.editor_errors[path] = message
        self.app.query_one("#editor-error", Static).update(message)

    def clear_editor_error(self, path: str) -> None:
        self.state.editor_errors.pop(path, None)
        self.app.query_one("#editor-error", Static).update("")

    def finish_successful_change(
        self,
        node: FieldNode,
        validated: BaseModel,
    ) -> None:
        self.state.data = validated.model_dump(mode="json")
        self.persist_validated_data(validated)
        self.clear_editor_error(node.dotted_path)
        self.state.validation_errors = {}
        self.app.rebuild_tree()
        self.app.load_node(node)
        self.app.focus_tree_at_current_path()

    def cancel_current_edit(self) -> None:
        node = self.current_node()
        if node is None:
            return
        self.clear_editor_error(node.dotted_path)
        self.app.load_node(node)
        self.app.focus_tree_at_current_path()

    def activate_tree_node(self) -> None:
        tree = self.app.query_one("#config-tree", Tree)
        cursor_node = tree.cursor_node
        if cursor_node is None:
            return
        dotted_path = cursor_node.data
        if not isinstance(dotted_path, str):
            return
        node = self.app.node_lookup.get(dotted_path)
        if node is None:
            return
        self.app.load_node(node)
        if node.is_section:
            if not cursor_node.is_expanded:
                cursor_node.expand()
            return
        self.app.call_after_refresh(self.app.focus_current_editor_input)

    def apply_current_edit(self) -> None:
        self.apply_current_field(refocus_on_error=True)

    def apply_current_field(self, refocus_on_error: bool = False) -> None:
        node = self.current_node()
        if node is None:
            return
        raw = self.app.current_editor().get_raw_value()
        try:
            value = coerce_value(node, raw)
        except (ValueError, json.JSONDecodeError) as error:
            self.set_editor_error(node.dotted_path, str(error))
            self.state.validation_errors = {}
            self.app.refresh_tree_node_label(node)
            if refocus_on_error:
                self.app.focus_current_editor_input()
            return

        runtime_error = self.runtime_validation_error(node, value)
        if runtime_error is not None:
            self.set_editor_error(node.dotted_path, runtime_error)
            self.state.validation_errors = {}
            self.app.refresh_tree_node_label(node)
            if refocus_on_error:
                self.app.focus_current_editor_input()
            return

        candidate_errors = self.candidate_validation_errors(node.path, value)
        if candidate_errors:
            self.set_editor_error(
                node.dotted_path,
                candidate_errors.get(
                    node.dotted_path,
                    "This value is not valid.",
                ),
            )
            self.state.validation_errors = candidate_errors
            self.app.refresh_tree_node_label(node)
            if refocus_on_error:
                self.app.focus_current_editor_input()
            return

        self.state.editor_errors.pop(node.dotted_path, None)
        set_value(self.state.data, node.path, value)
        validated = self.validate_data()
        self.finish_successful_change(node, validated)

    def reset_field(self) -> None:
        node = self.current_node()

        if node is None:
            return

        default = default_value(node.field_info)

        if isinstance(default, BaseModel):
            default = default.model_dump(mode="json")
        elif default is not None:
            default = json_safe(default)

        self.clear_editor_error(node.dotted_path)

        set_value(self.state.data, node.path, default)

        try:
            validated = self.validate_data()
        except ValidationError:
            self.state.validation_errors = self.collect_validation_errors()
        else:
            self.finish_successful_change(node, validated)
            return

        self.app.rebuild_tree()
        self.app.load_node(node)
        self.app.focus_tree_at_current_path()

    def export_json(self) -> None:
        try:
            validated = self.validate_data()
        except ValidationError as error:
            self.app.push_screen(MessageScreen("Cannot export", str(error)))
            return
        self.app.push_screen(
            MessageScreen(
                "Current configuration",
                validated.model_dump_json(indent=2),
            ),
        )

    def finish(self) -> None:
        try:
            validated = self.validate_data()
        except ValidationError as error:
            self.app.push_screen(MessageScreen("Cannot save", str(error)))
            return
        self.app.exit(validated)
