"""Settings screen for Yaade configuration."""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, List

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll, Grid
from textual.widgets import Label, Button, Input, Static, Select, DataTable, OptionList
from textual.widgets.option_list import Option
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding


class StorageConfigScreen(ModalScreen[Optional[str]]):
    """Modal screen for configuring storage location."""

    CSS = """
    StorageConfigScreen {
        align: center middle;
    }

    #dialog {
        width: 70;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
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

    Input:focus {
        border: tall $accent;
    }

    .help-text {
        color: $text-muted;
        margin-bottom: 1;
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
        with Container(id="dialog"):
            yield Label("Configure Storage Location", id="title")
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
            with Horizontal(id="buttons"):
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


class SetupResultScreen(ModalScreen[bool]):
    """Modal screen to show setup script results."""

    CSS = """
    SetupResultScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: 30;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }

    #output {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }

    #buttons {
        height: auto;
    }

    Button {
        margin: 0 1;
    }

    Button:focus {
        text-style: bold reverse;
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
            yield Label(f"{self.title_text} - {status}", id="title")
            with VerticalScroll(id="output"):
                yield Static(self.output_text)
            with Horizontal(id="buttons"):
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


class ThemeSelectScreen(ModalScreen[Optional[str]]):
    """Modal screen for selecting app theme with live preview."""

    # Available Textual themes
    THEMES = [
        ("textual-dark", "Textual Dark"),
        ("textual-light", "Textual Light"),
        ("nord", "Nord"),
        ("gruvbox", "Gruvbox"),
        ("catppuccin-mocha", "Catppuccin Mocha"),
        ("catppuccin-latte", "Catppuccin Latte"),
        ("dracula", "Dracula"),
        ("monokai", "Monokai"),
        ("tokyo-night", "Tokyo Night"),
        ("solarized-light", "Solarized Light"),
        ("solarized-dark", "Solarized Dark"),
    ]

    CSS = """
    ThemeSelectScreen {
        align: center middle;
    }

    #dialog {
        width: 90;
        height: 28;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }

    #theme-content {
        height: 1fr;
    }

    #theme-list-container {
        width: 30;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }

    #theme-list {
        height: 100%;
    }

    #preview-container {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 1;
        margin-left: 1;
    }

    #preview-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .preview-section {
        margin-bottom: 1;
    }

    .preview-label {
        color: $text-muted;
    }

    #preview-table {
        height: 6;
        margin-bottom: 1;
    }

    #preview-buttons {
        height: auto;
    }

    #preview-buttons Button {
        margin-right: 1;
    }

    #buttons {
        height: auto;
        margin-top: 1;
        dock: bottom;
    }

    Button {
        margin: 0 1;
    }

    Button:focus {
        text-style: bold reverse;
    }

    OptionList:focus {
        border: tall $accent;
    }

    OptionList > .option-list--option-highlighted {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("enter", "select_theme", "Select", show=False),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_theme: str):
        """Initialize with current theme."""
        super().__init__()
        self.current_theme = current_theme
        self.selected_theme = current_theme

    def compose(self) -> ComposeResult:
        """Compose the theme selection dialog."""
        with Container(id="dialog"):
            yield Label("Select Theme", id="title")

            with Horizontal(id="theme-content"):
                # Theme list on the left
                with Container(id="theme-list-container"):
                    yield OptionList(
                        *[Option(name, id=theme_id) for theme_id, name in self.THEMES],
                        id="theme-list"
                    )

                # Preview panel on the right
                with Vertical(id="preview-container"):
                    yield Label("Preview", id="preview-title")

                    with Vertical(classes="preview-section"):
                        yield Label("Sample text in default color")
                        yield Label("Muted text appears like this", classes="preview-label")

                    yield DataTable(id="preview-table")

                    with Horizontal(id="preview-buttons"):
                        yield Button("Primary", variant="primary")
                        yield Button("Default", variant="default")
                        yield Button("Error", variant="error")

            with Horizontal(id="buttons"):
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set up the preview table and initial selection."""
        # Set up preview table
        table = self.query_one("#preview-table", DataTable)
        table.add_columns("ID", "Content", "Tags")
        table.add_row("abc123", "Sample memory content...", "tag1, tag2")
        table.add_row("def456", "Another memory entry", "example")
        table.cursor_type = "row"

        # Focus theme list and highlight current theme
        option_list = self.query_one("#theme-list", OptionList)
        option_list.focus()

        # Find and highlight current theme
        for i, (theme_id, _) in enumerate(self.THEMES):
            if theme_id == self.current_theme:
                option_list.highlighted = i
                break

    @on(OptionList.OptionHighlighted, "#theme-list")
    def on_theme_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Preview theme when highlighted."""
        if event.option and event.option.id:
            self.selected_theme = str(event.option.id)
            self.app.theme = self.selected_theme

    def action_cursor_up(self) -> None:
        """Move cursor up in theme list."""
        self.query_one("#theme-list", OptionList).action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down in theme list."""
        self.query_one("#theme-list", OptionList).action_cursor_down()

    def action_select_theme(self) -> None:
        """Apply the currently highlighted theme."""
        self.dismiss(self.selected_theme)

    @on(Button.Pressed, "#apply")
    def handle_apply(self) -> None:
        """Handle apply button press."""
        self.dismiss(self.selected_theme)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        # Restore original theme
        self.app.theme = self.current_theme
        self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle escape key."""
        self.handle_cancel()


class SettingsScreen(ModalScreen[bool]):
    """Settings screen for server configuration."""

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }

    .section {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    .info-text {
        color: $text-muted;
        margin-bottom: 1;
    }

    .welcome-text {
        color: $accent;
        text-style: bold;
        text-align: center;
        margin-bottom: 2;
    }

    .onboarding-text {
        color: $text;
        text-align: center;
        margin-bottom: 2;
    }

    Button {
        margin: 0 1 1 1;
    }

    Button:focus {
        text-style: bold reverse;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("up,k", "focus_previous", "Up", show=False),
        Binding("down,j", "focus_next", "Down", show=False),
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
        self.query_one("#storage_config", Button).focus()

    def action_focus_previous(self) -> None:
        """Move focus to previous button."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to next button."""
        self.focus_next()

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with Container(id="dialog"):
            # Show welcome message for first-time setup
            if self.is_first_run:
                yield Label("Welcome to Yaade!", classes="welcome-text")
                yield Label(
                    "Let's set up your memory storage location and configure MCP integration.",
                    classes="onboarding-text"
                )

            yield Label("Yaade Settings", id="title")

            # Storage configuration section
            with Vertical(classes="section"):
                yield Label("Storage Configuration", classes="section-title")
                yield Label(
                    f"Current: {self.config_data.get('data_dir', 'N/A')}",
                    classes="info-text"
                )
                if self.is_first_run:
                    yield Label(
                        "Choose where to store your memories (optional - default is '.yaade')",
                        classes="info-text"
                    )
                yield Button("Change Storage Location", id="storage_config", variant="default")

            # MCP Integration section
            with Vertical(classes="section"):
                yield Label("MCP Integration Setup", classes="section-title")
                yield Label(
                    "Configure Yaade for Claude Desktop or Claude Code",
                    classes="info-text"
                )
                if self.is_first_run:
                    yield Label(
                        "Run these setup scripts to integrate with your Claude client (optional)",
                        classes="info-text"
                    )
                yield Button("Setup for Claude Desktop", id="setup_claude_desktop", variant="primary")
                yield Button("Setup for Claude Code", id="setup_claude_code", variant="primary")

            # Server info section
            with Vertical(classes="section"):
                yield Label("Server Information", classes="section-title")
                yield Label(f"Embedding Model: {self.config_data.get('embedding_model', 'N/A')}")
                yield Label(f"Host: {self.config_data.get('host', 'localhost')}")
                yield Label(f"Port: {self.config_data.get('port', '8000')}")

            # Theme section
            with Vertical(classes="section"):
                yield Label("Appearance", classes="section-title")
                current_theme = self.config_data.get('theme', 'textual-dark')
                yield Label(f"Current theme: {current_theme}", classes="info-text", id="current-theme-label")
                yield Button("Change Theme", id="theme_config", variant="default")

            with Horizontal(id="buttons"):
                if self.is_first_run:
                    yield Button("Continue to Memory Management", variant="primary", id="back")
                else:
                    yield Button("Back to Main Menu", variant="default", id="back")

    @on(Button.Pressed, "#storage_config")
    async def handle_storage_config(self) -> None:
        """Handle storage configuration."""
        current_path = self.config_data.get('data_dir', '.yaade')

        def callback(new_path: Optional[str]) -> None:
            if new_path is not None:
                self.update_storage_path(new_path)

        await self.app.push_screen(StorageConfigScreen(current_path), callback)

    def update_storage_path(self, new_path: str) -> None:
        """Update storage path in .env file."""
        try:
            env_path = Path.cwd() / '.env'

            # Read existing .env or create new one
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()

            # Update or add YAADE_DATA_DIR
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith('YAADE_DATA_DIR='):
                    env_lines[i] = f'YAADE_DATA_DIR={new_path}\n'
                    found = True
                    break

            if not found:
                env_lines.append(f'YAADE_DATA_DIR={new_path}\n')

            # Write back
            with open(env_path, 'w') as f:
                f.writelines(env_lines)

            self.app.notify(
                f"Storage location updated to: {new_path}\nRestart the server for changes to take effect.",
                severity="information",
                timeout=5
            )
            self.config_data['data_dir'] = new_path

        except Exception as e:
            self.app.notify(f"Failed to update storage location: {str(e)}", severity="error")

    @on(Button.Pressed, "#theme_config")
    async def handle_theme_config(self) -> None:
        """Handle theme configuration."""
        current_theme = self.config_data.get('theme', self.app.theme or 'textual-dark')

        def callback(new_theme: Optional[str]) -> None:
            if new_theme is not None:
                self.update_theme(new_theme)

        await self.app.push_screen(ThemeSelectScreen(current_theme), callback)

    def update_theme(self, new_theme: str) -> None:
        """Update theme in .env file and apply it."""
        try:
            env_path = Path.cwd() / '.env'

            # Read existing .env or create new one
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()

            # Update or add YAADE_THEME
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith('YAADE_THEME='):
                    env_lines[i] = f'YAADE_THEME={new_theme}\n'
                    found = True
                    break

            if not found:
                env_lines.append(f'YAADE_THEME={new_theme}\n')

            # Write back
            with open(env_path, 'w') as f:
                f.writelines(env_lines)

            # Apply theme immediately
            self.app.theme = new_theme
            self.config_data['theme'] = new_theme

            # Update the label
            theme_label = self.query_one("#current-theme-label", Label)
            theme_label.update(f"Current theme: {new_theme}")

            self.app.notify(f"Theme changed to: {new_theme}", severity="information")

        except Exception as e:
            self.app.notify(f"Failed to update theme: {str(e)}", severity="error")

    @on(Button.Pressed, "#setup_claude_desktop")
    async def handle_setup_claude_desktop(self) -> None:
        """Handle Claude Desktop setup."""
        self.app.notify("Running Claude Desktop setup script...", severity="information")

        # Determine OS and script path
        os_type = platform.system()
        if os_type == "Darwin":  # macOS
            script_path = Path.cwd() / "setup" / "claude-desktop" / "setup-mcp-macos.sh"
        elif os_type == "Windows":
            script_path = Path.cwd() / "setup" / "claude-desktop" / "setup-mcp-windows.bat"
        else:
            self.app.notify("Unsupported OS for automatic setup", severity="error")
            return

        if not script_path.exists():
            self.app.notify(f"Setup script not found: {script_path}", severity="error")
            return

        # Run setup script
        try:
            if os_type == "Darwin":
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:  # Windows
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=True
                )

            output = result.stdout + "\n" + result.stderr
            success = result.returncode == 0

            await self.app.push_screen(
                SetupResultScreen("Claude Desktop Setup", output, success)
            )

        except subprocess.TimeoutExpired:
            self.app.notify("Setup script timed out", severity="error")
        except Exception as e:
            self.app.notify(f"Setup failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#setup_claude_code")
    async def handle_setup_claude_code(self) -> None:
        """Handle Claude Code setup."""
        self.app.notify("Running Claude Code setup script...", severity="information")

        # Determine OS and script path
        os_type = platform.system()
        if os_type == "Darwin":  # macOS
            script_path = Path.cwd() / "setup" / "claude-code" / "setup-mcp-macos.sh"
        elif os_type == "Windows":
            script_path = Path.cwd() / "setup" / "claude-code" / "setup-mcp-windows.bat"
        else:
            self.app.notify("Unsupported OS for automatic setup", severity="error")
            return

        if not script_path.exists():
            self.app.notify(f"Setup script not found: {script_path}", severity="error")
            return

        # Run setup script
        try:
            if os_type == "Darwin":
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:  # Windows
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=True
                )

            output = result.stdout + "\n" + result.stderr
            success = result.returncode == 0

            await self.app.push_screen(
                SetupResultScreen("Claude Code Setup", output, success)
            )

        except subprocess.TimeoutExpired:
            self.app.notify("Setup script timed out", severity="error")
        except Exception as e:
            self.app.notify(f"Setup failed: {str(e)}", severity="error")

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
