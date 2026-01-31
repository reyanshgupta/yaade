"""Storage configuration modal screen."""

import os
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Button, Input
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding


class StorageConfigScreen(ModalScreen[Optional[str]]):
    """Modal screen for configuring storage location."""

    CSS_PATH = [
        Path(__file__).parent.parent.parent / "styles" / "modal.tcss",
    ]

    CSS = """
    StorageConfigScreen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, current_path: str):
        """Initialize with current storage path."""
        super().__init__()
        self.current_path = current_path

    def compose(self) -> ComposeResult:
        """Compose the storage config dialog."""
        with Container(id="dialog", classes="modal-dialog-narrow"):
            yield Label("Configure Storage Location", id="title", classes="modal-title")
            yield Label(
                "Current: " + self.current_path,
                classes="help-text"
            )
            yield Label("Enter new storage directory path:")
            yield Input(
                placeholder="e.g., ~/.yaade or /path/to/storage",
                id="storage_path",
                value=self.current_path
            )
            yield Label(
                "Tip: Use ~ for home directory. Path will be created if it doesn't exist.",
                classes="help-text"
            )
            with Horizontal(id="buttons", classes="modal-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set initial focus on path input."""
        self.query_one("#storage_path", Input).focus()

    @on(Button.Pressed, "#save")
    async def handle_save(self) -> None:
        """Handle save button press."""
        path_input = self.query_one("#storage_path", Input)
        new_path = path_input.value.strip()

        if not new_path:
            self.app.notify("Path cannot be empty", severity="error")
            return

        # Expand user path
        expanded_path = os.path.expanduser(new_path)
        self.dismiss(expanded_path)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)

    async def action_save(self) -> None:
        """Handle Ctrl+S keyboard shortcut."""
        await self.handle_save()

    def action_cancel(self) -> None:
        """Handle Escape keyboard shortcut."""
        self.handle_cancel()
