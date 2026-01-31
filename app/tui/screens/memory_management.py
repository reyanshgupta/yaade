"""Memory management screen."""

from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, DataTable
from textual.binding import Binding
from textual.screen import Screen
from textual import on

from .modals import (
    AddMemoryScreen, AddMemoryResult,
    EditMemoryScreen, EditMemoryResult,
    ThemeSelectScreen,
)

if TYPE_CHECKING:
    from ..app import Yaade


class MemoryManagementScreen(Screen["Yaade"]):
    """Screen for memory management operations."""

    CSS_PATH = [
        Path(__file__).parent.parent / "styles" / "screens.tcss",
    ]

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

        # Save cursor position before deletion
        cursor_row = table.cursor_row
        memory = self.memories[cursor_row]
        memory_id = memory["memory_id"]

        app = cast("Yaade", self.app)
        self.app.notify("Deleting memory...")
        response = await app.manager.delete_memory(memory_id)

        if response.get("status") == "deleted":
            self.app.notify("Memory deleted successfully", severity="information")
            await self.refresh_memories()
            # Restore cursor position (adjust if we deleted the last row)
            new_row_count = len(self.memories)
            if new_row_count > 0:
                new_cursor_row = min(cursor_row, new_row_count - 1)
                table.move_cursor(row=new_cursor_row)
        else:
            self.app.notify(f"Failed to delete memory: {response.get('error', 'Unknown error')}", severity="error")

    async def action_refresh(self) -> None:
        """Refresh the memory list."""
        self.app.notify("Refreshing...", severity="information")
        await self.refresh_memories()

    def action_settings(self) -> None:
        """Show settings dialog."""
        from ..settings import SettingsScreen
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
