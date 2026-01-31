"""Main Textual TUI application for memory management."""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll, Center
from textual.widgets import Header, Footer, Static, Input, Button, DataTable, Label
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual import on
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING, cast
import asyncio
import os
from pathlib import Path

from .memory_manager import MemoryManager
from .settings import SettingsScreen, ThemeSelectScreen
from .themes import CUSTOM_THEMES

# Type alias for add memory result
AddMemoryResult = Tuple[str, List[str], float]
# Type alias for edit memory result  
EditMemoryResult = Tuple[str, str, List[str], float]

if TYPE_CHECKING:
    from typing import TypeAlias
    # Forward reference for type checking only
    YaadeType: TypeAlias = "Yaade"


class AddMemoryScreen(ModalScreen[Optional[AddMemoryResult]]):
    """Modal screen for adding a new memory."""

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


class EditMemoryScreen(ModalScreen[Optional[EditMemoryResult]]):
    """Modal screen for editing an existing memory."""

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


class MainMenuScreen(Screen["Yaade"]):
    """Main menu screen for the application."""

    CSS = """
    MainMenuScreen {
        align: center middle;
    }

    #main-container {
        width: 50;
        height: auto;
        background: $surface;
        border: heavy $primary;
        padding: 1 2;
    }

    #logo {
        color: $primary;
        text-style: bold;
        text-align: center;
        width: 100%;
    }

    #tagline {
        color: $secondary;
        text-style: italic;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .menu-button {
        width: 100%;
        margin-bottom: 1;
    }

    #footer-text {
        color: $text-muted;
        text-align: center;
        width: 100%;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("up,k", "focus_previous", "Up", show=False),
        Binding("down,j", "focus_next", "Down", show=False),
        Binding("1", "memory_management", "Memories"),
        Binding("2", "settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main menu."""
        yield Header()
        with Center():
            with Container(id="main-container"):
                yield Static("Y A A D E", id="logo")
                yield Static("central memory for all your AI tools", id="tagline")
                yield Button("[1] Memories", id="memory_mgmt", classes="menu-button", variant="primary")
                yield Button("[2] Settings", id="settings", classes="menu-button", variant="default")
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
        app = cast("Yaade", self.app)
        self.app.push_screen(SettingsScreen(app._get_config_data()))

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class MemoryManagementScreen(Screen["Yaade"]):
    """Screen for memory management operations."""

    CSS = """
    MemoryManagementScreen {
        background: $background;
    }

    #main-content {
        height: 1fr;
    }

    #stats {
        height: auto;
        background: $panel;
        border-bottom: heavy $primary;
        padding: 1;
        color: $secondary;
    }

    #memories {
        height: 1fr;
        border: double $primary;
        background: $surface;
    }

    #memories-container {
        height: 1fr;
        padding: 1;
    }

    DataTable {
        height: 100%;
        background: $surface;
    }

    DataTable > .datatable--header {
        background: $panel;
        color: $primary;
        text-style: bold;
    }

    DataTable > .datatable--cursor {
        background: $primary;
        color: $background;
        text-style: bold;
    }

    DataTable > .datatable--hover {
        background: $secondary 30%;
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
        Binding("ctrl+p", "open_theme", "Theme"),
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
        with Vertical(id="main-content"):
            yield Static("Loading statistics...", id="stats")
            with Container(id="memories-container"):
                yield DataTable(id="memories")
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
        app = cast("Yaade", self.app)
        stats = await app.manager.get_stats()
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
        app = cast("Yaade", self.app)
        self.memories = await app.manager.list_all_memories(limit=50)

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

    async def handle_add_memory(self, result: Optional[AddMemoryResult]) -> None:
        """Handle add memory result."""
        if result is None:
            return

        content, tags, importance = result

        app = cast("Yaade", self.app)
        self.app.notify("Adding memory...")
        response = await app.manager.add_memory(
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

    async def handle_edit_memory(self, result: Optional[EditMemoryResult]) -> None:
        """Handle edit memory result."""
        if result is None:
            return

        memory_id, content, tags, importance = result

        app = cast("Yaade", self.app)
        self.app.notify("Updating memory...")
        response = await app.manager.update_memory(
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

        app = cast("Yaade", self.app)
        self.app.notify("Deleting memory...")
        response = await app.manager.delete_memory(memory_id)

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
        app = cast("Yaade", self.app)
        self.app.push_screen(SettingsScreen(app._get_config_data()))

    def action_open_theme(self) -> None:
        """Open theme selector (ctrl+p)."""
        app = cast("Yaade", self.app)
        current_theme = app.theme or 'cyberpunk'

        def callback(new_theme: Optional[str]) -> None:
            if new_theme is not None:
                app.theme = new_theme
                app._save_theme(new_theme)
                app.notify(f"Theme changed to: {new_theme}", severity="information")

        self.app.push_screen(ThemeSelectScreen(current_theme), callback)

    def action_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class Yaade(App):
    """A Textual TUI for memory management."""

    TITLE = "yaade"
    ENABLE_COMMAND_PALETTE = False  # Disable built-in command palette

    BINDINGS = [
        Binding("ctrl+p", "open_theme_selector", "Themes", show=False),
    ]

    CSS = """
    Screen {
        background: $background;
    }

    /* Global cyberpunk styling enhancements */
    Header {
        background: $panel;
        color: $primary;
        text-style: bold;
    }

    Footer {
        background: $panel;
    }

    Footer > .footer--key {
        background: $primary;
        color: $background;
    }

    Footer > .footer--description {
        color: $secondary;
    }

    /* Button styling */
    Button {
        border: tall $primary;
        color: $text;
    }

    Button:hover {
        background: $primary 20%;
        border: tall $secondary;
    }

    Button:focus {
        text-style: bold reverse;
    }

    Button.-primary {
        background: $primary;
        color: #0a0a12;
        border: tall $primary;
        text-style: bold;
    }

    Button.-primary:hover {
        background: $primary 80%;
        border: tall $secondary;
    }

    Button.-error {
        background: $error;
        color: #0a0a12;
        border: tall $error;
        text-style: bold;
    }

    /* Input styling */
    Input {
        border: tall $primary;
        background: $surface;
    }

    Input:focus {
        border: tall $secondary;
        background: $panel;
    }

    /* DataTable global styling */
    DataTable {
        scrollbar-color: $primary;
        scrollbar-color-hover: $secondary;
        scrollbar-background: $surface;
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
            Theme name, defaults to 'cyberpunk'
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
        return 'cyberpunk'  # Default to cyberpunk theme

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Register custom themes
        for theme in CUSTOM_THEMES:
            self.register_theme(theme)

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

    def action_open_theme_selector(self) -> None:
        """Open the theme selector with live preview."""
        current_theme = self.theme or 'cyberpunk'
        self.push_screen(ThemeSelectScreen(current_theme), self._handle_theme_change)

    def _handle_theme_change(self, new_theme: Optional[str]) -> None:
        """Handle theme selection result."""
        if new_theme is not None:
            self._save_theme(new_theme)

    def _save_theme(self, theme: str) -> None:
        """Save theme to .env file."""
        env_path = Path.cwd() / '.env'
        env_lines = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_lines = f.readlines()

        found = False
        for i, line in enumerate(env_lines):
            if line.startswith('YAADE_THEME='):
                env_lines[i] = f'YAADE_THEME={theme}\n'
                found = True
                break

        if not found:
            env_lines.append(f'YAADE_THEME={theme}\n')

        with open(env_path, 'w') as f:
            f.writelines(env_lines)

        self.notify(f"Theme changed to: {theme}", severity="information")

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

    def _handle_first_run_complete(self, result: Optional[bool]) -> None:
        """Handle completion of first-time setup.

        Args:
            result: True if setup completed, False/None if cancelled
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
    app = Yaade()
    app.run()
