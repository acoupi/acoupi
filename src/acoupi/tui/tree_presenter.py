"""Tree rendering helpers for the Textual config TUI."""

from __future__ import annotations

from typing import Any

from textual.widgets import Tree

from .models import FieldNode
from .utils import get_value, summarize_value


class TreePresenter:
    """Builds and updates the configuration tree from app state."""

    def __init__(self, app: Any) -> None:
        self.app = app

    def branch_has_error(self, path: tuple[str, ...]) -> bool:
        prefix = ".".join(path)
        return any(
            error == prefix or error.startswith(f"{prefix}.")
            for error in self.app.validation_errors
        )

    def format_label(self, node: FieldNode) -> str:
        if node.is_section:
            marker = (
                "[red]![/red]"
                if self.branch_has_error(node.path)
                else "[cyan]+[/cyan]"
            )
            return f"{marker} {node.title}"

        value = get_value(self.app.data, node.path)
        if node.dotted_path in self.app.editor_errors or self.branch_has_error(
            node.path
        ):
            indicator = "[red]![/red]"
        elif value is None and node.required:
            indicator = "[yellow]?[/yellow]"
        else:
            indicator = "[green]•[/green]"
        return f"{indicator} {node.title}: {summarize_value(value)}"

    def expand_to_path(self, dotted_path: str) -> None:
        parts = dotted_path.split(".")
        for size in range(1, len(parts)):
            prefix = ".".join(parts[:size])
            branch = self.app._tree_paths.get(prefix)
            if branch is not None:
                branch.expand()

    def rebuild(self) -> None:
        tree = self.app.query_one("#config-tree", Tree)
        tree.clear()
        tree.root.label = "Configuration"
        tree.root.expand()
        self.app._tree_paths = {}

        branch_index: dict[tuple[str, ...], Any] = {(): tree.root}
        for node in self.app.nodes:
            parent = branch_index[node.path[:-1]]
            branch = parent.add(
                self.format_label(node),
                data=node.dotted_path,
            )
            self.app._tree_paths[node.dotted_path] = branch
            if node.is_section:
                branch.allow_expand = True
                branch.collapse()
                branch_index[node.path] = branch
            else:
                branch.allow_expand = False

        if (
            self.app.current_path
            and self.app.current_path in self.app._tree_paths
        ):
            self.expand_to_path(self.app.current_path)
            tree.select_node(self.app._tree_paths[self.app.current_path])

    def refresh_node_label(self, node: FieldNode) -> None:
        tree_node = self.app._tree_paths.get(node.dotted_path)
        if tree_node is not None:
            tree_node.set_label(self.format_label(node))
