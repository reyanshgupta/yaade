"""Add memory modal screen."""

from pathlib import Path
from typing import Optional, List, Tuple

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, Input
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding


# Type alias for add memory result
AddMemoryResult = Tuple[str, List[str], float]


class AddMemoryScreen(ModalScreen[Optional[AddMemoryResult]]):
    """Modal screen for adding a new memory."""

    CSS_PATH = [
        Path(__file__).parent.parent.parent / "styles" / "modal.tcss",
    ]

    CSS = """
    AddMemoryScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: auto;
        border: double $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    Label {
        color: $secondary;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }

    Button:focus {
        text-style: bold reverse;
    }

    Input {
        border: tall $primary;
        background: $panel;
    }

    Input:focus {
        border: tall $secondary;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "submit", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the add memory dialog."""
        with Container(id="dialog"):
            yield Label("[ ADD NEW MEMORY ]", id="title")
            yield Label("Content:")
            yield Input(placeholder="Enter memory content...", id="content")
            yield Label("Tags (comma-separated):")
            yield Input(placeholder="tag1, tag2, tag3", id="tags")
            yield Label("Importance (0-10):")
            yield Input(placeholder="1.0", id="importance", value="1.0")
            with Horizontal(id="buttons"):
                yield Button("[ ADD ]", variant="primary", id="add")
                yield Button("[ CANCEL ]", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set initial focus on content input."""
        self.query_one("#content", Input).focus()

    @on(Button.Pressed, "#add")
    async def handle_add(self) -> None:
        """Handle add button press."""
        content_input = self.query_one("#content", Input)
        tags_input = self.query_one("#tags", Input)
        importance_input = self.query_one("#importance", Input)

        content = content_input.value.strip()
        if not content:
            self.app.notify("Content cannot be empty", severity="error")
            return

        tags = [tag.strip() for tag in tags_input.value.split(",") if tag.strip()]

        try:
            importance = float(importance_input.value or "1.0")
            if not 0 <= importance <= 10:
                raise ValueError()
        except ValueError:
            self.app.notify("Importance must be a number between 0 and 10", severity="error")
            return

        self.dismiss((content, tags, importance))

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)

    async def action_submit(self) -> None:
        """Handle Ctrl+S keyboard shortcut."""
        await self.handle_add()

    def action_cancel(self) -> None:
        """Handle Escape keyboard shortcut."""
        self.handle_cancel()
