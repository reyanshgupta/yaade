"""Main Textual TUI application for memory management."""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, DataTable, Label
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual import on
from typing import Optional, List, Dict, Any
import asyncio

from .memory_manager import MemoryManager


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
    """

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
    """

    def __init__(self, memory: Dict[str, Any]):
        """Initialize with memory data."""
        super().__init__()
        self.memory = memory

    def compose(self) -> ComposeResult:
        """Compose the edit memory dialog."""
        metadata = self.memory.get("metadata", {})
        tags = metadata.get("tags", [])
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
                value=", ".join(tags) if tags else "",
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


class SearchScreen(ModalScreen[str]):
    """Modal screen for searching memories."""

    CSS = """
    SearchScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
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
    """

    def compose(self) -> ComposeResult:
        """Compose the search dialog."""
        with Container(id="dialog"):
            yield Label("Search Memories", id="title")
            yield Label("Enter search query:")
            yield Input(placeholder="Search...", id="query")
            with Horizontal(id="buttons"):
                yield Button("Search", variant="primary", id="search")
                yield Button("Cancel", variant="default", id="cancel")

    @on(Button.Pressed, "#search")
    async def handle_search(self) -> None:
        """Handle search button press."""
        query_input = self.query_one("#query", Input)
        query = query_input.value.strip()

        if not query:
            self.app.notify("Please enter a search query", severity="error")
            return

        self.dismiss(query)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)


class MemoryTUI(App):
    """A Textual TUI for memory management."""

    CSS = """
    Screen {
        background: $background;
    }

    #stats {
        height: 3;
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
    """

    BINDINGS = [
        Binding("a", "add_memory", "Add"),
        Binding("e", "edit_memory", "Edit"),
        Binding("d", "delete_memory", "Delete"),
        Binding("s", "search_memory", "Search"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        """Initialize the TUI."""
        super().__init__()
        self.manager = MemoryManager()
        self.memories: List[Dict[str, Any]] = []
        self.current_query: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
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

        await self.refresh_stats()
        await self.refresh_memories()

    async def refresh_stats(self) -> None:
        """Refresh the statistics display."""
        stats = await self.manager.get_stats()
        stats_widget = self.query_one("#stats", Static)
        stats_widget.update(
            f"Total Memories: {stats.get('total_memories', 0)} | "
            f"Model: {stats.get('embedding_model', 'N/A')} | "
            f"Data: {stats.get('data_directory', 'N/A')}"
        )

    async def refresh_memories(self) -> None:
        """Refresh the memory list."""
        table = self.query_one(DataTable)
        table.clear()

        if self.current_query:
            # Search mode
            self.memories = await self.manager.search_memories(self.current_query, limit=50)
        else:
            # List all mode
            self.memories = await self.manager.list_all_memories(limit=50)

        for memory in self.memories:
            metadata = memory.get("metadata", {})
            tags = ", ".join(metadata.get("tags", []))
            importance = metadata.get("importance", 1.0)
            content = memory.get("content", "")

            # Truncate content for display
            display_content = content[:50] + "..." if len(content) > 50 else content

            table.add_row(
                memory["memory_id"][:8],
                display_content,
                tags or "-",
                str(importance)
            )

        await self.refresh_stats()

    def action_add_memory(self) -> None:
        """Show add memory dialog."""
        self.push_screen(AddMemoryScreen(), self.handle_add_memory)

    async def handle_add_memory(self, result: Optional[tuple]) -> None:
        """Handle add memory result."""
        if result is None:
            return

        content, tags, importance = result

        self.notify("Adding memory...")
        response = await self.manager.add_memory(
            content=content,
            tags=tags,
            importance=importance
        )

        if response.get("status") == "added":
            self.notify("Memory added successfully", severity="information")
            await self.refresh_memories()
        else:
            self.notify(f"Failed to add memory: {response.get('error', 'Unknown error')}", severity="error")

    def action_edit_memory(self) -> None:
        """Show edit memory dialog."""
        table = self.query_one(DataTable)

        if table.cursor_row < 0 or table.cursor_row >= len(self.memories):
            self.notify("Please select a memory to edit", severity="warning")
            return

        memory = self.memories[table.cursor_row]
        self.push_screen(EditMemoryScreen(memory), self.handle_edit_memory)

    async def handle_edit_memory(self, result: Optional[tuple]) -> None:
        """Handle edit memory result."""
        if result is None:
            return

        memory_id, content, tags, importance = result

        self.notify("Updating memory...")
        response = await self.manager.update_memory(
            memory_id=memory_id,
            content=content,
            tags=tags,
            importance=importance
        )

        if response.get("status") == "added":
            self.notify("Memory updated successfully", severity="information")
            await self.refresh_memories()
        else:
            self.notify(f"Failed to update memory: {response.get('error', 'Unknown error')}", severity="error")

    async def action_delete_memory(self) -> None:
        """Delete the selected memory."""
        table = self.query_one(DataTable)

        if table.cursor_row < 0 or table.cursor_row >= len(self.memories):
            self.notify("Please select a memory to delete", severity="warning")
            return

        memory = self.memories[table.cursor_row]
        memory_id = memory["memory_id"]

        self.notify("Deleting memory...")
        response = await self.manager.delete_memory(memory_id)

        if response.get("status") == "deleted":
            self.notify("Memory deleted successfully", severity="information")
            await self.refresh_memories()
        else:
            self.notify(f"Failed to delete memory: {response.get('error', 'Unknown error')}", severity="error")

    def action_search_memory(self) -> None:
        """Show search dialog."""
        self.push_screen(SearchScreen(), self.handle_search)

    async def handle_search(self, query: Optional[str]) -> None:
        """Handle search result."""
        if query is None:
            return

        self.current_query = query
        self.notify(f"Searching for: {query}", severity="information")
        await self.refresh_memories()

    async def action_refresh(self) -> None:
        """Refresh the memory list."""
        self.current_query = None  # Clear search
        self.notify("Refreshing...", severity="information")
        await self.refresh_memories()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui() -> None:
    """Run the TUI application."""
    app = MemoryTUI()
    app.run()
