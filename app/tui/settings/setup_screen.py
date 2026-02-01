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
from ..widgets import CollapsibleItem


# MCP Integration configuration - easy to extend with new integrations!
INTEGRATIONS = [
    {
        "title": "Claude Desktop",
        "description": "Configure Yaade as an MCP server for Claude Desktop app",
        "button_text": "Setup for Claude Desktop",
        "button_id": "setup_claude_desktop",
        "client_type": "claude-desktop",
    },
    {
        "title": "Claude Code",
        "description": "Configure Yaade as an MCP server for Claude Code CLI",
        "button_text": "Setup for Claude Code",
        "button_id": "setup_claude_code",
        "client_type": "claude-code",
    },
    {
        "title": "OpenCode",
        "description": "Configure Yaade as an MCP server for OpenCode",
        "button_text": "Setup for OpenCode",
        "button_id": "setup_opencode",
        "client_type": "opencode",
    },
]


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
        # Build a mapping from button_id to client_type for dynamic handling
        self._button_to_client = {
            integration["button_id"]: integration["client_type"]
            for integration in INTEGRATIONS
        }

    def on_mount(self) -> None:
        """Set initial focus on the first collapsible item."""
        # Focus the first CollapsibleItem instead of a button
        first_item = self.query(CollapsibleItem).first()
        if first_item:
            first_item.focus()

    def action_focus_previous(self) -> None:
        """Move focus to previous focusable element."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to next focusable element."""
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

            # MCP Integrations as collapsible accordion
            # Compact display - expands on focus, collapses on blur
            with Vertical(classes="integrations-container"):
                yield Label("Select an integration to configure:", classes="integrations-title")
                for integration in INTEGRATIONS:
                    yield CollapsibleItem(
                        title=integration["title"],
                        description=integration["description"],
                        button_text=integration["button_text"],
                        button_id=integration["button_id"],
                    )

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

    @on(Button.Pressed)
    async def handle_integration_setup(self, event: Button.Pressed) -> None:
        """Handle any integration setup button press dynamically."""
        button_id = event.button.id
        
        # Check if this is an integration button
        if button_id in self._button_to_client:
            client_type = self._button_to_client[button_id]
            await self._run_setup(client_type)

    async def _run_setup(self, client_type: str) -> None:
        """Run setup for the specified client type.
        
        Args:
            client_type: The client type identifier (e.g., 'claude-desktop')
        """
        display_name = SetupRunner.get_client_display_name(client_type)
        self.app.notify(f"Running {display_name} setup script...", severity="information")
        
        result = SetupRunner.run_setup(client_type)
        
        if result.error:
            self.app.notify(f"{display_name} setup failed: {result.error}", severity="error")
            return
        
        # Notify user of completion status
        if result.success:
            self.app.notify(f"{display_name} setup completed successfully!", severity="information")
        else:
            self.app.notify(f"{display_name} setup completed with issues", severity="warning")
        
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
