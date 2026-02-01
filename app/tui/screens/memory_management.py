"""Memory management screen."""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.coordinate import Coordinate
from textual.widgets import Header, Footer, Static, DataTable
from textual.binding import Binding
from textual.screen import Screen
from textual.worker import Worker, get_current_worker
from textual import on, work

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
        Binding("d", "delete_memory", "Delete (dd)"),
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
        # Track pending delete confirmation (row index and timestamp)
        self._pending_delete_row: Optional[int] = None
        self._pending_delete_time: float = 0.0
        # Timeout for confirmation (in seconds)
        self._delete_confirm_timeout: float = 2.0

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
        # Add columns with explicit widths - Content gets most space
        table.add_column("ID", width=10)
        table.add_column("Content", width=None)  # Auto-expand to fill space
        table.add_column("Tags", width=20)
        table.add_column("Importance", width=12)
        table.focus()

        await self.refresh_stats()
        await self.refresh_memories()

    def on_screen_resume(self) -> None:
        """Restore focus when returning to this screen."""
        self.query_one(DataTable).focus()
        # Reset pending delete when returning to screen
        self._reset_pending_delete()

    def action_cursor_up(self) -> None:
        """Move cursor up in the table."""
        table = self.query_one(DataTable)
        table.action_cursor_up()
        # Reset pending delete when cursor moves
        self._reset_pending_delete()

    def action_cursor_down(self) -> None:
        """Move cursor down in the table."""
        table = self.query_one(DataTable)
        table.action_cursor_down()
        # Reset pending delete when cursor moves
        self._reset_pending_delete()

    def _reset_pending_delete(self) -> None:
        """Reset the pending delete state and restore row content if needed."""
        if self._pending_delete_row is not None:
            self._restore_row_content(self._pending_delete_row)
        self._pending_delete_row = None
        self._pending_delete_time = 0.0

    def _restore_row_content(self, row_index: int) -> None:
        """Restore the original content of a row after pending delete is cancelled."""
        if row_index < 0 or row_index >= len(self.memories):
            return
        
        table = self.query_one(DataTable)
        memory = self.memories[row_index]
        content = memory.get("content", "")
        
        # Recreate the original display content
        display_content = content[:200] + "..." if len(content) > 200 else content
        display_content = display_content.replace("\n", " ").replace("\r", "")
        
        # Update the content column using coordinate (row, column)
        # Column 1 is "Content" (0=ID, 1=Content, 2=Tags, 3=Importance)
        table.update_cell_at(Coordinate(row_index, 1), display_content)

    def _show_delete_confirmation_in_row(self, row_index: int) -> None:
        """Update the row to show delete confirmation message."""
        if row_index < 0 or row_index >= len(self.memories):
            return
        
        table = self.query_one(DataTable)
        table.update_cell_at(Coordinate(row_index, 1), "⚠️  Press 'd' again to DELETE this memory  ⚠️")

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

            # Truncate content for display (show more content with line breaks preserved)
            display_content = content[:200] + "..." if len(content) > 200 else content
            # Replace newlines with spaces for table display
            display_content = display_content.replace("\n", " ").replace("\r", "")

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

    def handle_add_memory(self, result: Optional[AddMemoryResult]) -> None:
        """Handle add memory result."""
        if result is None:
            return

        content, tags, importance = result

        self.app.notify("Adding memory...")

        # Generate embedding on main thread to avoid PyTorch file descriptor issues
        app = cast("Yaade", self.app)
        try:
            embedding = app.manager.generate_embedding_sync(content)
        except Exception as e:
            self.app.notify(f"Failed to generate embedding: {e}", severity="error")
            return

        # Use worker to run storage operation in thread (safe without PyTorch)
        self._run_store_memory(content, embedding, tags, importance)

    @work(thread=True)
    def _run_store_memory(self, content: str, embedding: list, tags: list, importance: float) -> None:
        """Run store memory in a worker thread (embedding already computed)."""
        try:
            app = cast("Yaade", self.app)
            response = app.manager.store_memory_with_embedding_sync(
                content=content,
                embedding=embedding,
                tags=tags,
                importance=importance
            )

            # Post result back to main thread
            self.app.call_from_thread(self._handle_add_memory_result, response)
        except Exception as e:
            # Handle unexpected exceptions
            error_response = {"status": "failed", "error": str(e)}
            self.app.call_from_thread(self._handle_add_memory_result, error_response)

    def _handle_add_memory_result(self, response: dict) -> None:
        """Handle add memory result on main thread."""
        if response.get("status") == "added":
            self.app.notify("Memory added successfully", severity="information")
            # Refresh memories
            self._run_refresh_memories()
        else:
            self.app.notify(f"Failed to add memory: {response.get('error', 'Unknown error')}", severity="error")

    @work(thread=True)
    def _run_refresh_memories(self) -> None:
        """Run refresh memories in a worker thread."""
        try:
            app = cast("Yaade", self.app)
            memories = app.manager.list_all_memories_sync(limit=50)
            self.app.call_from_thread(self._update_memories_table, memories)
        except Exception as e:
            # Show error to user instead of silently failing
            self.app.call_from_thread(
                self.app.notify,
                f"Failed to refresh: {e}",
                severity="error"
            )

    def _update_memories_table(self, memories: list) -> None:
        """Update the memories table on main thread."""
        self.memories = memories
        table = self.query_one(DataTable)
        table.clear()
        
        for memory in self.memories:
            metadata = memory.get("metadata", {})
            tags_data = metadata.get("tags", "")
            tags = tags_data.replace(",", ", ") if tags_data else "-"
            importance = metadata.get("importance", 1.0)
            content = memory.get("content", "")

            display_content = content[:200] + "..." if len(content) > 200 else content
            display_content = display_content.replace("\n", " ").replace("\r", "")

            table.add_row(
                memory["memory_id"][:8],
                display_content,
                tags,
                str(importance)
            )
        
        # Also refresh stats
        self._run_refresh_stats()

    @work(thread=True)
    def _run_refresh_stats(self) -> None:
        """Run refresh stats in a worker thread."""
        try:
            app = cast("Yaade", self.app)
            stats = app.manager.get_stats_sync()
            self.app.call_from_thread(self._update_stats, stats)
        except Exception:
            # Silently fail stats refresh
            pass

    def _update_stats(self, stats: dict) -> None:
        """Update stats display on main thread."""
        stats_widget = self.query_one("#stats", Static)
        stats_widget.update(
            f"Total Memories: {stats.get('total_memories', 0)} | "
            f"Model: {stats.get('embedding_model', 'N/A')}\n"
            f"Storage: {stats.get('storage_location', 'N/A')} ({stats.get('storage_size', 'N/A')})"
        )

    def action_edit_memory(self) -> None:
        """Show edit memory dialog."""
        table = self.query_one(DataTable)

        if table.cursor_row < 0 or table.cursor_row >= len(self.memories):
            self.app.notify("Please select a memory to edit", severity="warning")
            return

        memory = self.memories[table.cursor_row]
        self.app.push_screen(EditMemoryScreen(memory), self.handle_edit_memory)

    def handle_edit_memory(self, result: Optional[EditMemoryResult]) -> None:
        """Handle edit memory result."""
        if result is None:
            return

        memory_id, content, tags, importance = result

        self.app.notify("Updating memory...")

        # Generate embedding on main thread to avoid PyTorch file descriptor issues
        app = cast("Yaade", self.app)
        try:
            embedding = app.manager.generate_embedding_sync(content)
        except Exception as e:
            self.app.notify(f"Failed to generate embedding: {e}", severity="error")
            return

        # Use worker to run storage operation in thread (safe without PyTorch)
        self._run_update_memory_with_embedding(memory_id, content, embedding, tags, importance)

    @work(thread=True)
    def _run_update_memory_with_embedding(
        self, memory_id: str, content: str, embedding: list, tags: list, importance: float
    ) -> None:
        """Run update memory in a worker thread (embedding already computed)."""
        try:
            app = cast("Yaade", self.app)
            response = app.manager.update_memory_with_embedding_sync(
                memory_id=memory_id,
                content=content,
                embedding=embedding,
                tags=tags,
                importance=importance
            )
            self.app.call_from_thread(self._handle_update_memory_result, response)
        except Exception as e:
            error_response = {"status": "failed", "error": str(e)}
            self.app.call_from_thread(self._handle_update_memory_result, error_response)

    def _handle_update_memory_result(self, response: dict) -> None:
        """Handle update memory result on main thread."""
        if response.get("status") == "added":
            self.app.notify("Memory updated successfully", severity="information")
            self._run_refresh_memories()
        else:
            self.app.notify(f"Failed to update memory: {response.get('error', 'Unknown error')}", severity="error")

    def action_delete_memory(self) -> None:
        """Delete the selected memory (requires pressing 'd' twice to confirm)."""
        table = self.query_one(DataTable)

        if table.cursor_row < 0 or table.cursor_row >= len(self.memories):
            self.app.notify("Please select a memory to delete", severity="warning")
            return

        cursor_row = table.cursor_row
        current_time = time.time()

        # Check if this is a confirmation press (same row, within timeout)
        if (self._pending_delete_row == cursor_row and 
            current_time - self._pending_delete_time < self._delete_confirm_timeout):
            # This is the confirmation - proceed with deletion
            self._pending_delete_row = None
            self._pending_delete_time = 0.0

            memory = self.memories[cursor_row]
            memory_id = memory["memory_id"]

            self.app.notify("Deleting memory...")
            self._run_delete_memory(memory_id, cursor_row)
        else:
            # First press - set pending delete and show confirmation prompt
            self._pending_delete_row = cursor_row
            self._pending_delete_time = current_time
            
            # Update the row to show confirmation message
            self._show_delete_confirmation_in_row(cursor_row)
            
            memory = self.memories[cursor_row]
            content_preview = memory.get("content", "")[:30]
            if len(memory.get("content", "")) > 30:
                content_preview += "..."
            
            self.app.notify(
                f"Press 'd' again to delete: \"{content_preview}\"",
                severity="warning",
                timeout=self._delete_confirm_timeout
            )

    @work(thread=True)
    def _run_delete_memory(self, memory_id: str, cursor_row: int) -> None:
        """Run delete memory in a worker thread."""
        try:
            app = cast("Yaade", self.app)
            response = app.manager.delete_memory_sync(memory_id)
            self.app.call_from_thread(self._handle_delete_memory_result, response, cursor_row)
        except Exception as e:
            error_response = {"status": "error", "error": str(e)}
            self.app.call_from_thread(self._handle_delete_memory_result, error_response, cursor_row)

    def _handle_delete_memory_result(self, response: dict, cursor_row: int) -> None:
        """Handle delete memory result on main thread."""
        if response.get("status") == "deleted":
            self.app.notify("Memory deleted successfully", severity="information")
            self._run_refresh_memories()
            # Note: cursor position will be handled after refresh
        else:
            self.app.notify(f"Failed to delete memory: {response.get('error', 'Unknown error')}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the memory list."""
        self.app.notify("Refreshing...", severity="information")
        self._run_refresh_memories()

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
