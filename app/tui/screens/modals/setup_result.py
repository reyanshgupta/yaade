"""Setup result modal screen."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Label, Button, Static
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding


class SetupResultScreen(ModalScreen[bool]):
    """Modal screen to show setup script results."""

    CSS_PATH = [
        Path(__file__).parent.parent.parent / "styles" / "modal.tcss",
    ]

    CSS = """
    SetupResultScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: 30;
        border: double $primary;
        background: $surface;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("escape,enter", "close", "Close"),
    ]

    def __init__(self, title: str, output: str, success: bool):
        """Initialize with setup results."""
        super().__init__()
        self.title_text = title
        self.output_text = output
        self.success = success

    def compose(self) -> ComposeResult:
        """Compose the result dialog."""
        status = "Success" if self.success else "Error"
        with Container(id="dialog"):
            yield Label(f"{self.title_text} - {status}", id="title", classes="modal-title")
            with VerticalScroll(id="output", classes="modal-output"):
                yield Static(self.output_text)
            with Horizontal(id="buttons", classes="modal-buttons"):
                yield Button("Close", variant="primary", id="close")

    def on_mount(self) -> None:
        """Set initial focus on close button."""
        self.query_one("#close", Button).focus()

    @on(Button.Pressed, "#close")
    def handle_close(self) -> None:
        """Handle close button press."""
        self.dismiss(True)

    def action_close(self) -> None:
        """Handle keyboard shortcut to close."""
        self.handle_close()
