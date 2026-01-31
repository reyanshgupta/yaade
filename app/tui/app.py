"""Main Textual TUI application for memory management."""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll, Center
from textual.widgets import Header, Footer, Static, Input, Button, DataTable, Label
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual import on
from typing import Optional, List, Dict, Any
import asyncio
import os
from pathlib import Path

from .memory_manager import MemoryManager
from .settings import SettingsScreen


class AddMemoryScreen(ModalScreen[bool]):
    """Modal screen for adding a new memory."""

    CSS = """
    AddMemoryScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
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
    """

    BINDINGS = [
        Binding("ctrl+s", "submit", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the add memory dialog."""
        with Container(id="dialog"):
            yield Label("Add New Memory", id="title")
            yield Label("Content:")
            yield Input(placeholder="Enter memory content...", id="content")
            yield Label("Tags (comma-separated):")
            yield Input(placeholder="tag1, tag2, tag3", id="tags")
            yield Label("Importance (0-10):")
            yield Input(placeholder="1.0", id="importance", value="1.0")
            with Horizontal(id="buttons"):
                yield Button("Add", variant="primary", id="add")
                yield Button("Cancel", variant="default", id="cancel")

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


class EditMemoryScreen(ModalScreen[bool]):
    """Modal screen for editing an existing memory."""

    CSS = """
    EditMemoryScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
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
            yield Label("Edit Memory", id="title")
            yield Label(f"ID: {self.memory['memory_id'][:8]}...")
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
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

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


class MainMenuScreen(Screen):
    """Main menu screen for the application."""

    CSS = """
    MainMenuScreen {
        align: center middle;
    }

    #main-container {
        width: 70;
        height: auto;
        background: $surface;
        padding: 1 2;
    }

    #logo-container {
        width: 100%;
        height: auto;
        content-align: center middle;
        padding: 1 0;
    }

    #logo {
        text-align: center;
        color: $accent;
    }

    #tagline {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #stats-container {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    #stats-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .stat-row {
        height: auto;
    }

    .stat-label {
        color: $text-muted;
        width: 20;
    }

    .stat-value {
        color: $text;
    }

    #menu-section {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    .menu-button {
        width: 100%;
        margin-bottom: 1;
    }

    .menu-button:focus {
        text-style: bold reverse;
    }

    #footer-text {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("up,k", "focus_previous", "Up", show=False),
        Binding("down,j", "focus_next", "Down", show=False),
        Binding("1", "memory_management", "Memory Management"),
        Binding("2", "settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main menu."""
        yield Header()
        with Center():
            with Container(id="main-container"):
                # Logo section
                with Container(id="logo-container"):
                    yield Static(
                        """
╦ ╦┌─┐┌─┐┌┬┐┌─┐
╚╦╝├─┤├─┤ ││├┤ 
 ╩ ┴ ┴┴ ┴─┴┘└─┘
        """.strip(),
                        id="logo"
                    )
                    yield Label("Memory Storage for AI", id="tagline")

                # Stats section
                with Container(id="stats-container"):
                    yield Label("Quick Stats", id="stats-title")
                    with Horizontal(classes="stat-row"):
                        yield Label("Memories:", classes="stat-label")
                        yield Label("Loading...", id="stat-memories", classes="stat-value")
                    with Horizontal(classes="stat-row"):
                        yield Label("Storage:", classes="stat-label")
                        yield Label("Loading...", id="stat-storage", classes="stat-value")
                    with Horizontal(classes="stat-row"):
                        yield Label("Status:", classes="stat-label")
                        yield Label("Ready", id="stat-status", classes="stat-value")

                # Menu buttons
                with Container(id="menu-section"):
                    yield Button("Memories [1]", id="memory_mgmt", classes="menu-button", variant="primary")
                    yield Button("Settings [2]", id="settings", classes="menu-button", variant="default")
                    yield Button("Quit [Q]", id="quit", classes="menu-button", variant="error")

                yield Label("v0.1.0", id="footer-text")
        yield Footer()

    async def on_mount(self) -> None:
        """Set initial focus and load stats."""
        self.query_one("#memory_mgmt", Button).focus()
        await self._load_stats()

    async def on_screen_resume(self) -> None:
        """Refresh the screen and restore focus when it becomes visible again."""
        self.refresh(layout=True)
        self.query_one("#memory_mgmt", Button).focus()
        await self._load_stats()

    async def _load_stats(self) -> None:
        """Load and display statistics."""
        try:
            stats = await self.app.manager.get_stats()
            
            memories_label = self.query_one("#stat-memories", Label)
            storage_label = self.query_one("#stat-storage", Label)
            status_label = self.query_one("#stat-status", Label)
            
            memories_label.update(str(stats.get('total_memories', 0)))
            storage_label.update(f"{stats.get('storage_location', 'N/A')} ({stats.get('storage_size', 'N/A')})")
            status_label.update("Ready")
        except Exception:
            pass

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

    def action_settings(self) -> None:
        """Show settings dialog."""
        self.app.push_screen(SettingsScreen(self.app._get_config_data()))

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class MemoryManagementScreen(Screen):
    """Screen for memory management operations."""

    CSS = """
    #stats {
        height: 4;
        background: $boost;
        padding: 1;
    }

    #memories {
        height: 1fr;
        border: solid $primary;
    }

    DataTable {
        height: 100%;
    }

    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("enter", "edit_memory", "Edit", show=False),
        Binding("a", "add_memory", "Add"),
        Binding("e", "edit_memory", "Edit"),
        Binding("d", "delete_memory", "Delete"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "settings", "Settings"),
        Binding("escape", "back", "Back to Menu"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        """Initialize the memory management screen."""
        super().__init__()
        self.memories: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        """Compose the memory management screen."""
        yield Header()
        yield Container(
            Static("Loading statistics...", id="stats"),
            Container(
                DataTable(id="memories"),
                id="memories-container"
            )
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount event."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Content", "Tags", "Importance")
        table.focus()

        await self.refresh_stats()
        await self.refresh_memories()

    def on_screen_resume(self) -> None:
        """Restore focus when returning to this screen."""
        self.query_one(DataTable).focus()

    def action_cursor_up(self) -> None:
        """Move cursor up in the table."""
        table = self.query_one(DataTable)
        table.action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down in the table."""
        table = self.query_one(DataTable)
        table.action_cursor_down()

    async def refresh_stats(self) -> None:
        """Refresh the statistics display."""
        stats = await self.app.manager.get_stats()
        stats_widget = self.query_one("#stats", Static)
        stats_widget.update(
            f"Total Memories: {stats.get('total_memories', 0)} | "
            f"Model: {stats.get('embedding_model', 'N/A')}\n"
            f"Storage: {stats.get('storage_location', 'N/A')} ({stats.get('storage_size', 'N/A')})"
        )

    async def refresh_memories(self) -> None:
        """Refresh the memory list."""
        table = self.query_one(DataTable)
        table.clear()

        # Always list all memories (search removed)
        self.memories = await self.app.manager.list_all_memories(limit=50)

        for memory in self.memories:
            metadata = memory.get("metadata", {})
            # Tags are stored as comma-separated string in ChromaDB
            tags_data = metadata.get("tags", "")
            tags = tags_data.replace(",", ", ") if tags_data else "-"
            importance = metadata.get("importance", 1.0)
            content = memory.get("content", "")

            # Truncate content for display
            display_content = content[:50] + "..." if len(content) > 50 else content

            table.add_row(
                memory["memory_id"][:8],
                display_content,
                tags,
                str(importance)
            )

        await self.refresh_stats()

    def action_add_memory(self) -> None:
        """Show add memory dialog."""
        self.app.push_screen(AddMemoryScreen(), self.handle_add_memory)

    async def handle_add_memory(self, result: Optional[tuple]) -> None:
        """Handle add memory result."""
        if result is None:
            return

        content, tags, importance = result

        self.app.notify("Adding memory...")
        response = await self.app.manager.add_memory(
            content=content,
            tags=tags,
            importance=importance
        )

        if response.get("status") == "added":
            self.app.notify("Memory added successfully", severity="information")
            await self.refresh_memories()
        else:
            self.app.notify(f"Failed to add memory: {response.get('error', 'Unknown error')}", severity="error")

    def action_edit_memory(self) -> None:
        """Show edit memory dialog."""
        table = self.query_one(DataTable)

        if table.cursor_row < 0 or table.cursor_row >= len(self.memories):
            self.app.notify("Please select a memory to edit", severity="warning")
            return

        memory = self.memories[table.cursor_row]
        self.app.push_screen(EditMemoryScreen(memory), self.handle_edit_memory)

    async def handle_edit_memory(self, result: Optional[tuple]) -> None:
        """Handle edit memory result."""
        if result is None:
            return

        memory_id, content, tags, importance = result

        self.app.notify("Updating memory...")
        response = await self.app.manager.update_memory(
            memory_id=memory_id,
            content=content,
            tags=tags,
            importance=importance
        )

        if response.get("status") == "added":
            self.app.notify("Memory updated successfully", severity="information")
            await self.refresh_memories()
        else:
            self.app.notify(f"Failed to update memory: {response.get('error', 'Unknown error')}", severity="error")

    async def action_delete_memory(self) -> None:
        """Delete the selected memory."""
        table = self.query_one(DataTable)

        if table.cursor_row < 0 or table.cursor_row >= len(self.memories):
            self.app.notify("Please select a memory to delete", severity="warning")
            return

        memory = self.memories[table.cursor_row]
        memory_id = memory["memory_id"]

        self.app.notify("Deleting memory...")
        response = await self.app.manager.delete_memory(memory_id)

        if response.get("status") == "deleted":
            self.app.notify("Memory deleted successfully", severity="information")
            await self.refresh_memories()
        else:
            self.app.notify(f"Failed to delete memory: {response.get('error', 'Unknown error')}", severity="error")

    async def action_refresh(self) -> None:
        """Refresh the memory list."""
        self.app.notify("Refreshing...", severity="information")
        await self.refresh_memories()

    def action_settings(self) -> None:
        """Show settings dialog."""
        self.app.push_screen(SettingsScreen(self.app._get_config_data()))

    def action_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class MemoryTUI(App):
    """A Textual TUI for memory management."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    SCREENS = {
        "menu": MainMenuScreen,
        "memory_screen": MemoryManagementScreen,
    }

    def __init__(self):
        """Initialize the TUI."""
        super().__init__()
        # Check first run BEFORE creating MemoryManager (which creates directories)
        self.is_first_run = self._check_first_run()
        # Now initialize MemoryManager
        self.manager = MemoryManager()
        # Load saved theme
        self._saved_theme = self._load_theme()

    @staticmethod
    def _load_theme() -> str:
        """Load theme from .env file.

        Returns:
            Theme name, defaults to 'textual-dark'
        """
        env_path = Path.cwd() / '.env'
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        # Check both variable names for compatibility
                        if line.startswith('YAADE_THEME=') or line.startswith('MEMORY_SERVER_THEME='):
                            return line.strip().split('=', 1)[1]
            except Exception:
                pass
        return 'textual-dark'

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Apply saved theme
        self.theme = self._saved_theme

        if self.is_first_run:
            # First-time setup: show settings screen directly
            config_data = self._get_config_data()
            self.push_screen(SettingsScreen(config_data, is_first_run=True), self._handle_first_run_complete)
        else:
            # Already set up: go directly to memory management with menu in background
            self.push_screen("menu")
            self.push_screen("memory_screen")

    def _get_config_data(self) -> dict:
        """Get configuration data for settings screen."""
        return {
            'data_dir': str(self.manager.config.data_dir),
            'embedding_model': self.manager.config.embedding_model_name,
            'host': self.manager.config.host,
            'port': self.manager.config.port,
            'theme': self.theme or 'textual-dark',
        }

    @staticmethod
    def _check_first_run() -> bool:
        """Check if this is the first run (no directory setup completed).

        Returns:
            True if first run (needs setup), False if already configured
        """
        # Import here to avoid circular dependency
        from ..models.config import ServerConfig

        # Load config to get the configured paths (without creating directories)
        config = ServerConfig()
        data_dir = config.data_dir
        chroma_path = config.chroma_path

        # If chroma directory exists and has files, setup is complete
        if chroma_path.exists():
            try:
                # Check if directory has any files (not just .DS_Store)
                files = [f for f in chroma_path.iterdir() if not f.name.startswith('.')]
                if files:
                    return False  # Already set up
            except Exception:
                pass

        # If data directory exists and has any content, consider it set up
        if data_dir.exists():
            try:
                files = [f for f in data_dir.iterdir() if not f.name.startswith('.')]
                if files:
                    return False  # Already set up
            except Exception:
                pass

        # No setup found
        return True

    def _handle_first_run_complete(self, result: bool) -> None:
        """Handle completion of first-time setup.

        Args:
            result: True if setup completed, False if cancelled
        """
        if result:
            # Setup completed, show main menu first, then memory management
            # This ensures the user can navigate back properly
            self.push_screen("menu")
            self.push_screen("memory_screen")
        else:
            # Setup was cancelled, exit the app
            self.exit()


def run_tui() -> None:
    """Run the TUI application."""
    app = MemoryTUI()
    app.run()
