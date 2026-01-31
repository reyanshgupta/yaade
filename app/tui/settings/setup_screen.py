"""Setup screen for MCP integration configuration."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, Footer
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding

from ..screens.modals import StorageConfigScreen, SetupResultScreen, ThemeSelectScreen
from ..utils import ConfigManager, SetupRunner


class SetupScreen(ModalScreen[bool]):
    """Setup screen for MCP integration configuration."""

    CSS_PATH = [
        Path(__file__).parent.parent / "styles" / "settings.tcss",
    ]

    CSS = """
    SetupScreen {
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

    .welcome-text {
        height: auto;
        color: $primary;
        text-style: bold;
        text-align: center;
        margin-bottom: 2;
    }

    .onboarding-text {
        height: auto;
        color: $secondary;
        text-align: center;
        margin-bottom: 2;
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

    def __init__(self, config_data: dict, is_first_run: bool = False):
        """Initialize with current config.

        Args:
            config_data: Current configuration data
            is_first_run: True if this is first-time setup
        """
        super().__init__()
        self.config_data = config_data
        self.is_first_run = is_first_run

    def on_mount(self) -> None:
        """Set initial focus on the first button."""
        self.query_one("#setup_claude_desktop", Button).focus()

    def action_focus_previous(self) -> None:
        """Move focus to previous button."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to next button."""
        self.focus_next()

    def compose(self) -> ComposeResult:
        """Compose the setup screen."""
        with VerticalScroll(id="dialog"):
            # Show welcome message for first-time setup
            if self.is_first_run:
                yield Label("Welcome to Yaade!", classes="welcome-text")
                yield Label(
                    "Let's configure MCP integration with your Claude client.",
                    classes="onboarding-text"
                )

            yield Label("MCP Integration Setup", id="title")

            # Storage configuration section (only for first run)
            if self.is_first_run:
                with Vertical(classes="section"):
                    yield Label("Storage Configuration", classes="section-title")
                    yield Label(
                        f"Current: {self.config_data.get('data_dir', 'N/A')}",
                        classes="info-text"
                    )
                    yield Label(
                        "Choose where to store your memories (optional - default is '.yaade')",
                        classes="info-text"
                    )
                    yield Button("Change Storage Location", id="storage_config", variant="default")

            # MCP Integration section
            with Vertical(classes="section"):
                yield Label("Claude Desktop", classes="section-title")
                yield Label(
                    "Configure Yaade as an MCP server for Claude Desktop app",
                    classes="info-text"
                )
                yield Button("Setup for Claude Desktop", id="setup_claude_desktop", variant="primary")

            with Vertical(classes="section"):
                yield Label("Claude Code", classes="section-title")
                yield Label(
                    "Configure Yaade as an MCP server for Claude Code CLI",
                    classes="info-text"
                )
                yield Button("Setup for Claude Code", id="setup_claude_code", variant="primary")

            with Vertical(classes="section"):
                yield Label("OpenCode", classes="section-title")
                yield Label(
                    "Configure Yaade as an MCP server for OpenCode",
                    classes="info-text"
                )
                yield Button("Setup for OpenCode", id="setup_opencode", variant="primary")

            with Horizontal(id="buttons"):
                if self.is_first_run:
                    yield Button("Continue to Memory Management", variant="primary", id="back")
                else:
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

    @on(Button.Pressed, "#setup_claude_desktop")
    async def handle_setup_claude_desktop(self) -> None:
        """Handle Claude Desktop setup."""
        await self._run_setup("claude-desktop")

    @on(Button.Pressed, "#setup_claude_code")
    async def handle_setup_claude_code(self) -> None:
        """Handle Claude Code setup."""
        await self._run_setup("claude-code")

    @on(Button.Pressed, "#setup_opencode")
    async def handle_setup_opencode(self) -> None:
        """Handle OpenCode setup."""
        await self._run_setup("opencode")

    async def _run_setup(self, client_type: str) -> None:
        """Run setup for the specified client type.
        
        Args:
            client_type: Either 'claude-desktop', 'claude-code', or 'opencode'
        """
        display_name = SetupRunner.get_client_display_name(client_type)
        self.app.notify(f"Running {display_name} setup script...", severity="information")
        
        result = SetupRunner.run_setup(client_type)
        
        if result.error:
            self.app.notify(result.error, severity="error")
            return
        
        await self.app.push_screen(
            SetupResultScreen(f"{display_name} Setup", result.output, result.success)
        )

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

    async def action_open_theme(self) -> None:
        """Open theme selector (ctrl+p)."""
        current_theme = self.config_data.get('theme', self.app.theme or 'textual-dark')

        def callback(new_theme: Optional[str]) -> None:
            if new_theme is not None:
                ConfigManager.update_env_variable("YAADE_THEME", new_theme)
                self.app.theme = new_theme
                self.config_data['theme'] = new_theme
                self.app.notify(f"Theme changed to: {new_theme}", severity="information")

        await self.app.push_screen(ThemeSelectScreen(current_theme), callback)
