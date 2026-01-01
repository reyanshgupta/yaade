"""Settings screen for memory server configuration."""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, Input, Static
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

    .help-text {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

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
                placeholder="e.g., ~/.memory-server or /path/to/storage",
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
    """

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

    @on(Button.Pressed, "#close")
    def handle_close(self) -> None:
        """Handle close button press."""
        self.dismiss(True)


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

    #buttons {
        height: auto;
        margin-top: 1;
    }
    """

    BINDINGS = [
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

        # Override bindings for first-time setup
        if self.is_first_run:
            self.BINDINGS = [
                Binding("escape", "cancel", "Skip Setup"),
                Binding("q", "quit_app", "Quit"),
            ]

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with Container(id="dialog"):
            # Show welcome message for first-time setup
            if self.is_first_run:
                yield Label("Welcome to Memory Server for AI!", classes="welcome-text")
                yield Label(
                    "Let's set up your memory storage location and configure MCP integration.",
                    classes="onboarding-text"
                )

            yield Label("Memory Server Settings", id="title")

            # Storage configuration section
            with Vertical(classes="section"):
                yield Label("Storage Configuration", classes="section-title")
                yield Label(
                    f"Current: {self.config_data.get('data_dir', 'N/A')}",
                    classes="info-text"
                )
                if self.is_first_run:
                    yield Label(
                        "Choose where to store your memories (optional - default is '.memory-server')",
                        classes="info-text"
                    )
                yield Button("Change Storage Location", id="storage_config", variant="default")

            # MCP Integration section
            with Vertical(classes="section"):
                yield Label("MCP Integration Setup", classes="section-title")
                yield Label(
                    "Configure Memory Server for Claude Desktop or Claude Code",
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

            with Horizontal(id="buttons"):
                if self.is_first_run:
                    yield Button("Continue to Memory Management", variant="primary", id="back")
                else:
                    yield Button("Back to Main Menu", variant="default", id="back")

    @on(Button.Pressed, "#storage_config")
    async def handle_storage_config(self) -> None:
        """Handle storage configuration."""
        current_path = self.config_data.get('data_dir', '.memory-server')

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

            # Update or add MEMORY_SERVER_DATA_DIR
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith('MEMORY_SERVER_DATA_DIR='):
                    env_lines[i] = f'MEMORY_SERVER_DATA_DIR={new_path}\n'
                    found = True
                    break

            if not found:
                env_lines.append(f'MEMORY_SERVER_DATA_DIR={new_path}\n')

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
