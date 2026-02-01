"""Theme selection modal screen with live preview."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Static, DataTable, OptionList, Footer
from textual.widgets.option_list import Option
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding


class ThemeSelectScreen(ModalScreen[Optional[str]]):
    """Modal screen for selecting app theme with live preview."""

    # Available themes - Custom themes first, then built-in Textual themes
    THEMES = [
        # Custom cyberpunk themes
        ("cyberpunk", "Cyberpunk (Neon)"),
        ("cyberpunk-soft", "Cyberpunk Soft"),
        ("neon-nights", "Neon Nights"),
        # Built-in Textual themes
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

    # Theme descriptions for preview
    THEME_DESCRIPTIONS = {
        "cyberpunk": "Hot pink & electric cyan neons on dark blue-black",
        "cyberpunk-soft": "Softer cyberpunk colors for extended use",
        "neon-nights": "Vivid purple & bright teal with hot pink accents",
        "textual-dark": "Default dark theme with blue accents",
        "textual-light": "Clean light theme",
        "nord": "Arctic, north-bluish color palette",
        "gruvbox": "Retro groove colors with warm tones",
        "catppuccin-mocha": "Soothing pastel dark theme",
        "catppuccin-latte": "Soothing pastel light theme",
        "dracula": "Dark theme with purple accents",
        "monokai": "Iconic dark theme with vibrant colors",
        "tokyo-night": "Clean dark theme inspired by Tokyo lights",
        "solarized-light": "Precision colors for light backgrounds",
        "solarized-dark": "Precision colors for dark backgrounds",
    }

    CSS_PATH = [
        Path(__file__).parent.parent.parent / "styles" / "settings.tcss",
    ]

    CSS = """
    ThemeSelectScreen {
        align: center middle;
    }

    #dialog {
        width: 90;
        height: 24;
        border: double $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        height: auto;
        text-style: bold;
        color: $primary;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #theme-content {
        height: 1fr;
    }

    #theme-list-container {
        width: 30;
        height: 100%;
        border: heavy $primary;
        padding: 0 1;
        background: $panel;
    }

    #theme-list {
        height: 100%;
        background: $panel;
    }

    #preview-container {
        width: 1fr;
        height: 100%;
        border: heavy $secondary;
        padding: 1;
        margin-left: 1;
        background: $panel;
    }

    #preview-title {
        height: auto;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #theme-description {
        height: auto;
        color: $secondary;
        text-style: italic;
        margin-bottom: 1;
    }

    .preview-section {
        height: auto;
        margin-bottom: 1;
    }

    .preview-section Label {
        height: auto;
        color: $text;
    }

    .preview-label {
        color: $text-muted;
    }

    #color-swatches {
        height: 1;
        margin-bottom: 1;
    }

    .swatch {
        width: 8;
        height: 1;
        margin-right: 1;
        content-align: center middle;
    }

    #swatch-primary {
        background: $primary;
        color: $text;
    }

    #swatch-secondary {
        background: $secondary;
        color: $text;
    }

    #swatch-accent {
        background: $accent;
        color: $text;
    }

    #swatch-success {
        background: $success;
        color: $text;
    }

    #swatch-error {
        background: $error;
        color: $text;
    }

    #preview-table {
        height: 4;
        margin-bottom: 1;
        border: solid $primary;
    }

    #preview-buttons {
        height: auto;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    /* Button styling */
    Button {
        height: auto;
        min-width: 12;
    }

    Button.-primary {
        color: $background;
        background: $primary;
        text-style: bold;
    }

    Button.-default {
        color: $text;
        background: $surface;
        border: tall $primary;
    }

    Button.-error {
        color: $background;
        background: $error;
        text-style: bold;
    }

    Button:focus {
        text-style: bold reverse;
    }

    OptionList:focus {
        border: tall $accent;
    }

    OptionList > .option-list--option-highlighted {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    Footer {
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("enter", "select_theme", "Apply"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_theme: str):
        """Initialize with current theme."""
        super().__init__()
        self.current_theme = current_theme
        self.selected_theme = current_theme

    def compose(self) -> ComposeResult:
        """Compose the theme selection dialog."""
        with Vertical(id="dialog"):
            yield Label("[ SELECT THEME ]", id="title")

            with Horizontal(id="theme-content"):
                # Theme list on the left
                with Container(id="theme-list-container"):
                    yield OptionList(
                        *[Option(name, id=theme_id) for theme_id, name in self.THEMES],
                        id="theme-list"
                    )

                # Preview panel on the right
                with Vertical(id="preview-container"):
                    yield Label("LIVE PREVIEW", id="preview-title")
                    yield Label("", id="theme-description")

                    # Color swatches
                    with Horizontal(id="color-swatches"):
                        yield Static("PRIMARY", id="swatch-primary", classes="swatch")
                        yield Static("SECOND", id="swatch-secondary", classes="swatch")
                        yield Static("ACCENT", id="swatch-accent", classes="swatch")
                        yield Static("OK", id="swatch-success", classes="swatch")
                        yield Static("ERR", id="swatch-error", classes="swatch")

                    with Vertical(classes="preview-section"):
                        yield Label("Sample text in default color")
                        yield Label("Muted text appears like this", classes="preview-label")

                    yield DataTable(id="preview-table")

                    with Horizontal(id="preview-buttons"):
                        yield Button("Primary", variant="primary")
                        yield Button("Default", variant="default")
                        yield Button("Error", variant="error")

            with Horizontal(id="buttons", classes="modal-buttons"):
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Cancel", variant="default", id="cancel")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the preview table and initial selection."""
        # Set up preview table
        table = self.query_one("#preview-table", DataTable)
        table.add_columns("ID", "Content", "Tags")
        table.add_row("abc123", "Sample memory...", "tag1, tag2")
        table.add_row("def456", "Another entry", "example")
        table.cursor_type = "row"

        # Focus theme list and highlight current theme
        option_list = self.query_one("#theme-list", OptionList)
        option_list.focus()

        # Find and highlight current theme
        for i, (theme_id, _) in enumerate(self.THEMES):
            if theme_id == self.current_theme:
                option_list.highlighted = i
                break

        # Update description
        self._update_description(self.current_theme)

    def _update_description(self, theme_id: str) -> None:
        """Update the theme description label."""
        description = self.THEME_DESCRIPTIONS.get(theme_id, "")
        desc_label = self.query_one("#theme-description", Label)
        desc_label.update(description)

    @on(OptionList.OptionHighlighted, "#theme-list")
    def on_theme_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Preview theme when highlighted."""
        if event.option and event.option.id:
            self.selected_theme = str(event.option.id)
            self.app.theme = self.selected_theme
            self._update_description(self.selected_theme)

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
