"""Tree widget for the Textual config TUI."""

from __future__ import annotations

from textual.binding import Binding
from textual.widgets import Tree


def _call_app_method(app: object, name: str) -> None:
    handler = getattr(app, name, None)
    if callable(handler):
        handler()


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
        _call_app_method(self.app, "activate_tree_node")

    def action_collapse_current(self) -> None:
        node = self.cursor_node
        if node is None or not node.allow_expand:
            return
        if node.is_expanded:
            node.collapse()
