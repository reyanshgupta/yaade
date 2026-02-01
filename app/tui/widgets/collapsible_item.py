"""Collapsible accordion item widget for compact UI layouts."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Button, Label
from textual.reactive import reactive
from textual.widget import Widget
from textual import on


class CollapsibleItem(Widget, can_focus=True):
    """A collapsible accordion item that expands/collapses on Enter/Space.
    
    This widget provides a compact way to display multiple configuration
    options. Press Enter or Space to toggle between collapsed and expanded
    states. When expanded, shows description and action button.
    
    Navigation:
    - Arrow keys (up/down) or j/k: Navigate between items (collapses current)
    - Enter/Space when collapsed: Expand the item
    - Enter/Space when expanded: Activate the setup button
    
    Attributes:
        expanded: Whether the item is currently expanded.
        title: The title text shown in the header.
        description: Description shown when expanded.
        button_text: Text for the action button.
        button_id: ID for the action button (used for event handling).
    """
    
    expanded = reactive(False)
    
    DEFAULT_CSS = """
    CollapsibleItem {
        height: auto;
        width: 100%;
        margin-bottom: 0;
        border: solid $secondary;
        background: $panel;
    }
    
    CollapsibleItem:focus {
        border: solid $primary;
    }
    
    CollapsibleItem:focus .collapsible-header {
        background: $primary;
        color: $background;
    }
    
    .collapsible-header {
        height: auto;
        width: 100%;
        padding: 0 1;
        background: $panel;
    }
    
    .collapsible-header-text {
        height: auto;
        width: 100%;
    }
    
    .collapsible-content {
        height: auto;
        width: 100%;
        padding: 0 2 1 2;
        background: $surface;
        display: none;
    }
    
    CollapsibleItem.expanded .collapsible-content {
        display: block;
    }
    
    .collapsible-content .info-text {
        height: auto;
        color: $secondary;
        margin-bottom: 1;
    }
    
    .collapsible-content Button {
        margin: 0;
    }
    """
    
    BINDINGS = [
        ("enter", "toggle_or_activate", "Toggle/Setup"),
        ("space", "toggle_or_activate"),
        ("down", "navigate_next"),
        ("j", "navigate_next"),
        ("up", "navigate_previous"),
        ("k", "navigate_previous"),
    ]
    
    def __init__(
        self,
        title: str,
        description: str,
        button_text: str,
        button_id: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the collapsible item.
        
        Args:
            title: The title shown in the header row.
            description: Description text shown when expanded.
            button_text: Label for the action button.
            button_id: ID for the button (used for event handling).
            name: Optional widget name.
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._description = description
        self._button_text = button_text
        self._button_id = button_id
    
    def compose(self) -> ComposeResult:
        """Compose the collapsible item."""
        with Vertical(classes="collapsible-header"):
            yield Static(f"▶ {self._title}", classes="collapsible-header-text")
        with Vertical(classes="collapsible-content"):
            yield Label(self._description, classes="info-text")
            yield Button(self._button_text, id=self._button_id, variant="primary")
    
    def watch_expanded(self, expanded: bool) -> None:
        """Update UI when expanded state changes."""
        header_text = self.query_one(".collapsible-header-text", Static)
        
        if expanded:
            header_text.update(f"▼ {self._title}")
            self.add_class("expanded")
        else:
            header_text.update(f"▶ {self._title}")
            self.remove_class("expanded")
    
    def action_toggle_or_activate(self) -> None:
        """Toggle expand/collapse, or activate button if already expanded."""
        if self.expanded:
            # Already expanded - activate the button
            button = self.query_one(f"#{self._button_id}", Button)
            button.press()
        else:
            # Collapsed - expand it
            self.expanded = True
    
    def action_navigate_next(self) -> None:
        """Collapse current item and move focus to next focusable."""
        self.expanded = False
        self.screen.focus_next()
    
    def action_navigate_previous(self) -> None:
        """Collapse current item and move focus to previous focusable."""
        self.expanded = False
        self.screen.focus_previous()
    
    @on(Button.Pressed)
    def handle_button_press(self, event: Button.Pressed) -> None:
        """Let button press events bubble up to parent."""
        # Don't stop propagation - let parent handle the button press
        pass
