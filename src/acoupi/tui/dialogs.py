"""Dialogs for the Textual config TUI."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Static


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
