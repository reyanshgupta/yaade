"""Edit memory modal screen."""

from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, Input
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding


# Type alias for edit memory result
EditMemoryResult = Tuple[str, str, List[str], float]


class EditMemoryScreen(ModalScreen[Optional[EditMemoryResult]]):
    """Modal screen for editing an existing memory."""

    CSS_PATH = [
        Path(__file__).parent.parent.parent / "styles" / "modal.tcss",
    ]

    CSS = """
    EditMemoryScreen {
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

    #memory-id {
        color: $text-muted;
        text-style: italic;
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

    def __init__(self, memory: Dict[str, Any]):
        """Initialize with memory data."""
        super().__init__()
        self.memory = memory

    def compose(self) -> ComposeResult:
        """Compose the edit memory dialog."""
        metadata = self.memory.get("metadata", {})
        # Tags are stored as comma-separated string in ChromaDB
        tags_str = metadata.get("tags", "")
        # Add spaces after commas for better readability
        tags_display = tags_str.replace(",", ", ") if tags_str else ""
        importance = metadata.get("importance", 1.0)

        with Container(id="dialog"):
            yield Label("[ EDIT MEMORY ]", id="title")
            yield Label(f"ID: {self.memory['memory_id'][:8]}...", id="memory-id")
            yield Label("Content:")
            yield Input(
                value=self.memory.get("content", ""),
                id="content"
            )
            yield Label("Tags (comma-separated):")
            yield Input(
                value=tags_display,
                placeholder="tag1, tag2, tag3",
                id="tags"
            )
            yield Label("Importance (0-10):")
            yield Input(
                value=str(importance),
                placeholder="1.0",
                id="importance"
            )
            with Horizontal(id="buttons"):
                yield Button("[ SAVE ]", variant="primary", id="save")
                yield Button("[ CANCEL ]", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set initial focus on content input."""
        self.query_one("#content", Input).focus()

    @on(Button.Pressed, "#save")
    async def handle_save(self) -> None:
        """Handle save button press."""
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

        self.dismiss((self.memory["memory_id"], content, tags, importance))

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)

    async def action_submit(self) -> None:
        """Handle Ctrl+S keyboard shortcut."""
        await self.handle_save()

    def action_cancel(self) -> None:
        """Handle Escape keyboard shortcut."""
        self.handle_cancel()
