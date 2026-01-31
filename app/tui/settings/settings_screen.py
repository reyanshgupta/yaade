"""Settings screen for server configuration."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, Footer
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding

from ..screens.modals import StorageConfigScreen, ThemeSelectScreen
from ..utils import ConfigManager


class SettingsScreen(ModalScreen[bool]):
    """Settings screen for server configuration."""

    CSS_PATH = [
        Path(__file__).parent.parent / "styles" / "settings.tcss",
    ]

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: auto;
        max-height: 90%;
        border: double $primary;
        background: $surface;
        padding: 1;
        overflow-y: auto;
    }

    #title {
        height: auto;
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .section {
        height: auto;
        width: 100%;
        border: heavy $secondary;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }

    .section-title {
        height: auto;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }

    .info-text {
        height: auto;
        color: $secondary;
        margin-bottom: 1;
    }

    Label {
        height: auto;
        color: $secondary;
    }

    .section Label {
        color: $secondary;
    }

    Button {
        height: auto;
        margin: 0 1 1 1;
    }

    Button.-default {
        color: $secondary;
        background: $surface;
        border: tall $primary;
    }

    Button.-primary {
        color: $background;
        background: $primary;
        text-style: bold;
    }

    Button:focus {
        text-style: bold reverse;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    Footer {
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("up,k", "focus_previous", "Up", show=False),
        Binding("down,j", "focus_next", "Down", show=False),
        Binding("ctrl+p", "open_theme", "Theme"),
        Binding("escape", "cancel", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    def __init__(self, config_data: dict):
        """Initialize with current config.

        Args:
            config_data: Current configuration data
        """
        super().__init__()
        self.config_data = config_data

    def on_mount(self) -> None:
        """Set initial focus on the first button."""
        self.query_one("#storage_config", Button).focus()

    def action_focus_previous(self) -> None:
        """Move focus to previous button."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to next button."""
        self.focus_next()

    async def action_open_theme(self) -> None:
        """Open theme selector (ctrl+p)."""
        await self.handle_theme_config()

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with VerticalScroll(id="dialog"):
            yield Label("Settings", id="title")

            # Storage configuration section
            with Vertical(classes="section"):
                yield Label("Storage Configuration", classes="section-title")
                yield Label(
                    f"Current: {self.config_data.get('data_dir', 'N/A')}",
                    classes="info-text"
                )
                yield Button("Change Storage Location", id="storage_config", variant="default")

            # Server info section
            with Vertical(classes="section"):
                yield Label("Server Information", classes="section-title")
                yield Label(f"Embedding Model: {self.config_data.get('embedding_model', 'N/A')}", classes="info-text")
                yield Label(f"Host: {self.config_data.get('host', 'localhost')}", classes="info-text")
                yield Label(f"Port: {self.config_data.get('port', '8000')}", classes="info-text")

            # Theme section
            with Vertical(classes="section"):
                yield Label("Appearance", classes="section-title")
                current_theme = self.config_data.get('theme', 'textual-dark')
                yield Label(f"Current theme: {current_theme}", classes="info-text", id="current-theme-label")
                yield Button("Change Theme", id="theme_config", variant="default")

            with Horizontal(id="buttons"):
                yield Button("Back to Main Menu", variant="default", id="back")
        yield Footer()

    @on(Button.Pressed, "#storage_config")
    async def handle_storage_config(self) -> None:
        """Handle storage configuration."""
        current_path = self.config_data.get('data_dir', '.yaade')

        def callback(new_path: Optional[str]) -> None:
            if new_path is not None:
                self._update_storage_path(new_path)

        await self.app.push_screen(StorageConfigScreen(current_path), callback)

    def _update_storage_path(self, new_path: str) -> None:
        """Update storage path in .env file using ConfigManager."""
        success = ConfigManager.update_env_variable("YAADE_DATA_DIR", new_path)
        
        if success:
            self.app.notify(
                f"Storage location updated to: {new_path}\nRestart the server for changes to take effect.",
                severity="information",
                timeout=5
            )
            self.config_data['data_dir'] = new_path
        else:
            self.app.notify("Failed to update storage location", severity="error")

    @on(Button.Pressed, "#theme_config")
    async def handle_theme_config(self) -> None:
        """Handle theme configuration."""
        current_theme = self.config_data.get('theme', self.app.theme or 'textual-dark')

        def callback(new_theme: Optional[str]) -> None:
            if new_theme is not None:
                self._update_theme(new_theme)

        await self.app.push_screen(ThemeSelectScreen(current_theme), callback)

    def _update_theme(self, new_theme: str) -> None:
        """Update theme in .env file and apply it using ConfigManager."""
        success = ConfigManager.update_env_variable("YAADE_THEME", new_theme)
        
        if success:
            # Apply theme immediately
            self.app.theme = new_theme
            self.config_data['theme'] = new_theme

            # Update the label
            theme_label = self.query_one("#current-theme-label", Label)
            theme_label.update(f"Current theme: {new_theme}")

            self.app.notify(f"Theme changed to: {new_theme}", severity="information")
        else:
            self.app.notify("Failed to update theme", severity="error")

    @on(Button.Pressed, "#back")
    def handle_back(self) -> None:
        """Handle back button press."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Handle escape key."""
        self.dismiss(True)

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()
