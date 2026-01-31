"""Main menu screen."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.containers import Container, Center
from textual.widgets import Header, Footer, Static, Button, Label
from textual.binding import Binding
from textual.screen import Screen
from textual import on

if TYPE_CHECKING:
    from ..app import Yaade


class MainMenuScreen(Screen["Yaade"]):
    """Main menu screen for the application."""

    CSS_PATH = [
        Path(__file__).parent.parent / "styles" / "screens.tcss",
    ]

    CSS = """
    MainMenuScreen {
        align: center middle;
    }

    #main-container {
        width: 60;
        height: auto;
        background: $surface;
        border: heavy $primary;
        padding: 0 2;
    }

    #logo {
        color: $primary;
        text-style: bold;
        text-align: center;
        width: 100%;
        content-align: center middle;
    }

    #tagline {
        color: $secondary;
        text-style: italic;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        text-opacity: 70%;
    }

    .menu-button {
        width: 100%;
        margin-bottom: 1;
    }

    #footer-text {
        color: $text-muted;
        text-align: center;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("up,k", "focus_previous", "Up", show=False),
        Binding("down,j", "focus_next", "Down", show=False),
        Binding("1", "memory_management", "Memories"),
        Binding("2", "setup", "Setup"),
        Binding("3", "settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main menu."""
        # ASCII art for "yaade" - center aligned
        logo_art = (
            " _   _  __ _   __ _  __| | ___ \n"
            "| | | |/ _` | / _` |/ _` |/ _ \\\n"
            "| |_| | (_| || (_| | (_| |  __/\n"
            " \\__, |\\__,_| \\__,_|\\__,_|\\___|\n"
            " |___/                         "
        )

        yield Header()
        with Center():
            with Container(id="main-container"):
                yield Static(logo_art, id="logo")
                yield Static("memory for your AI tools", id="tagline")
                yield Button("[1] Memories", id="memory_mgmt", classes="menu-button", variant="default")
                yield Button("[2] Setup", id="setup", classes="menu-button", variant="default")
                yield Button("[3] Settings", id="settings", classes="menu-button", variant="default")
                yield Button("[Q] Exit", id="quit", classes="menu-button", variant="error")
                yield Label("v0.1.0", id="footer-text")
        yield Footer()

    def on_mount(self) -> None:
        """Set initial focus."""
        self.query_one("#memory_mgmt", Button).focus()

    def on_screen_resume(self) -> None:
        """Restore focus when returning to this screen."""
        self.refresh(layout=True)
        self.query_one("#memory_mgmt", Button).focus()

    def action_focus_previous(self) -> None:
        """Move focus to previous button."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to next button."""
        self.focus_next()

    @on(Button.Pressed, "#memory_mgmt")
    def handle_memory_mgmt(self) -> None:
        """Navigate to memory management."""
        self.action_memory_management()

    @on(Button.Pressed, "#setup")
    def handle_setup(self) -> None:
        """Navigate to setup."""
        self.action_setup()

    @on(Button.Pressed, "#settings")
    def handle_settings(self) -> None:
        """Navigate to settings."""
        self.action_settings()

    @on(Button.Pressed, "#quit")
    def handle_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_memory_management(self) -> None:
        """Switch to memory management screen."""
        self.app.push_screen("memory_screen")

    def action_setup(self) -> None:
        """Show setup dialog."""
        from ..settings import SetupScreen
        app = cast("Yaade", self.app)
        self.app.push_screen(SetupScreen(app._get_config_data()))

    def action_settings(self) -> None:
        """Show settings dialog."""
        from ..settings import SettingsScreen
        app = cast("Yaade", self.app)
        self.app.push_screen(SettingsScreen(app._get_config_data()))

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
