"""Settings screen for server configuration."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, Footer
from textual.screen import ModalScreen
from textual import on
from textual.binding import Binding

from ..screens.modals import StorageConfigScreen, ThemeSelectScreen, EmbeddingModelSelectScreen, get_model_by_id
from ..utils import ConfigManager
from ..widgets import CollapsibleItem


# Settings configuration - define all settings sections here
SETTINGS_ITEMS = [
    {
        "title": "Storage Configuration",
        "description": "Choose where to store your memories and data files.",
        "button_text": "Change Storage Location",
        "button_id": "storage_config",
        "info_key": "data_dir",
        "info_prefix": "Current: ",
        "info_default": "N/A",
    },
    {
        "title": "Embedding Model",
        "description": "Select the embedding model used for semantic search.",
        "button_text": "Change Embedding Model",
        "button_id": "embedding_config",
        "info_key": "embedding_model",
        "info_prefix": "Current: ",
        "info_default": "all-MiniLM-L6-v2",
    },
    {
        "title": "Appearance",
        "description": "Customize the visual theme of the application.",
        "button_text": "Change Theme",
        "button_id": "theme_config",
        "info_key": "theme",
        "info_prefix": "Current theme: ",
        "info_default": "textual-dark",
    },
]


class SettingsScreen(ModalScreen[bool]):
    """Settings screen for server configuration."""

    CSS_PATH = [
        Path(__file__).parent.parent / "styles" / "settings.tcss",
    ]

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: auto;
        max-height: 90%;
        border: double $primary;
        background: $surface;
        padding: 1;
        overflow-y: auto;
    }

    #title {
        height: auto;
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .section {
        height: auto;
        width: 100%;
        border: heavy $secondary;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }

    .section-title {
        height: auto;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }

    .info-text {
        height: auto;
        color: $secondary;
        margin-bottom: 1;
    }

    Label {
        height: auto;
        color: $secondary;
    }

    .section Label {
        color: $secondary;
    }

    Button {
        height: auto;
        margin: 0 1 1 1;
    }

    Button.-default {
        color: $secondary;
        background: $surface;
        border: tall $primary;
    }

    Button.-primary {
        color: $background;
        background: $primary;
        text-style: bold;
    }

    Button:focus {
        text-style: bold reverse;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    Footer {
        dock: bottom;
    }

    /* Collapsible accordion styles for settings */
    .settings-container {
        height: auto;
        width: 100%;
        border: solid $secondary;
        background: $panel;
        margin-bottom: 1;
    }

    .settings-label {
        height: auto;
        color: $secondary;
        text-style: italic;
        margin-bottom: 1;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("up,k", "focus_previous", "Up", show=False),
        Binding("down,j", "focus_next", "Down", show=False),
        Binding("ctrl+p", "open_theme", "Theme"),
        Binding("ctrl+e", "open_embedding", "Embedding"),
        Binding("escape", "cancel", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    def __init__(self, config_data: dict):
        """Initialize with current config.

        Args:
            config_data: Current configuration data
        """
        super().__init__()
        self.config_data = config_data
        # Build a mapping from button_id to handler for dynamic handling
        self._button_handlers = {
            "storage_config": self.handle_storage_config,
            "embedding_config": self.handle_embedding_config,
            "theme_config": self.handle_theme_config,
        }

    def on_mount(self) -> None:
        """Set initial focus on the first collapsible item."""
        first_item = self.query(CollapsibleItem).first()
        if first_item:
            first_item.focus()

    def action_focus_previous(self) -> None:
        """Move focus to previous focusable element."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to next focusable element."""
        self.focus_next()

    async def action_open_theme(self) -> None:
        """Open theme selector (ctrl+p)."""
        await self.handle_theme_config()

    async def action_open_embedding(self) -> None:
        """Open embedding model selector (ctrl+e)."""
        await self.handle_embedding_config()

    def _get_setting_description(self, setting: dict) -> str:
        """Build the description with current value for a setting.
        
        Args:
            setting: The setting configuration dict
            
        Returns:
            Description string with current value
        """
        base_desc = setting["description"]
        current_value = self.config_data.get(setting["info_key"], setting["info_default"])
        
        # Add extra info for embedding model
        if setting["button_id"] == "embedding_config":
            model_info = get_model_by_id(current_value)
            dimensions = model_info["dimensions"] if model_info else "Unknown"
            return f"{base_desc}\n{setting['info_prefix']}{current_value} ({dimensions} dimensions)"
        
        return f"{base_desc}\n{setting['info_prefix']}{current_value}"

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with VerticalScroll(id="dialog"):
            yield Label("Settings", id="title")

            # Settings as collapsible accordion items
            with Vertical(classes="settings-container"):
                yield Label("Select a setting to configure:", classes="settings-label")
                for setting in SETTINGS_ITEMS:
                    yield CollapsibleItem(
                        title=setting["title"],
                        description=self._get_setting_description(setting),
                        button_text=setting["button_text"],
                        button_id=setting["button_id"],
                    )

            # Server info section (read-only, no action needed)
            with Vertical(classes="section"):
                yield Label("Server Information", classes="section-title")
                yield Label(f"Host: {self.config_data.get('host', 'localhost')}", classes="info-text")
                yield Label(f"Port: {self.config_data.get('port', '8000')}", classes="info-text")

            with Horizontal(id="buttons"):
                yield Button("Back to Main Menu", variant="default", id="back")
        yield Footer()

    @on(Button.Pressed)
    async def handle_button_press(self, event: Button.Pressed) -> None:
        """Handle any settings button press dynamically."""
        button_id = event.button.id
        
        # Check if this is a settings button with a handler
        if button_id in self._button_handlers:
            await self._button_handlers[button_id]()

    async def handle_storage_config(self) -> None:
        """Handle storage configuration."""
        current_path = self.config_data.get('data_dir', '.yaade')

        def callback(new_path: Optional[str]) -> None:
            if new_path is not None:
                self._update_storage_path(new_path)

        await self.app.push_screen(StorageConfigScreen(current_path), callback)

    async def handle_embedding_config(self) -> None:
        """Handle embedding model configuration."""
        current_model = self.config_data.get('embedding_model', 'all-MiniLM-L6-v2')

        def callback(new_model: Optional[str]) -> None:
            if new_model is not None:
                self._update_embedding_model(new_model)

        await self.app.push_screen(EmbeddingModelSelectScreen(current_model), callback)

    def _update_storage_path(self, new_path: str) -> None:
        """Update storage path in .env file using ConfigManager."""
        success = ConfigManager.update_env_variable("YAADE_DATA_DIR", new_path)
        
        if success:
            self.app.notify(
                f"Storage location updated to: {new_path}\nRestart the server for changes to take effect.",
                severity="information",
                timeout=5
            )
            self.config_data['data_dir'] = new_path
            self._refresh_collapsible_descriptions()
        else:
            self.app.notify("Failed to update storage location", severity="error")

    def _update_embedding_model(self, new_model: str) -> None:
        """Update embedding model in .env file using ConfigManager."""
        success = ConfigManager.update_env_variable("YAADE_EMBEDDING_MODEL_NAME", new_model)
        
        if success:
            self.app.notify(
                f"Embedding model updated to: {new_model}\nRestart the server for changes to take effect.",
                severity="information",
                timeout=5
            )
            self.config_data['embedding_model'] = new_model
            self._refresh_collapsible_descriptions()
        else:
            self.app.notify("Failed to update embedding model", severity="error")

    async def handle_theme_config(self) -> None:
        """Handle theme configuration."""
        current_theme = self.config_data.get('theme', self.app.theme or 'textual-dark')

        def callback(new_theme: Optional[str]) -> None:
            if new_theme is not None:
                self._update_theme(new_theme)

        await self.app.push_screen(ThemeSelectScreen(current_theme), callback)

    def _update_theme(self, new_theme: str) -> None:
        """Update theme in .env file and apply it using ConfigManager."""
        success = ConfigManager.update_env_variable("YAADE_THEME", new_theme)
        
        if success:
            # Apply theme immediately
            self.app.theme = new_theme
            self.config_data['theme'] = new_theme
            self._refresh_collapsible_descriptions()
            self.app.notify(f"Theme changed to: {new_theme}", severity="information")
        else:
            self.app.notify("Failed to update theme", severity="error")

    def _refresh_collapsible_descriptions(self) -> None:
        """Refresh the descriptions in collapsible items after a setting change."""
        # Get all CollapsibleItems and update their descriptions
        for item in self.query(CollapsibleItem):
            # Find the matching setting config
            for setting in SETTINGS_ITEMS:
                if setting["button_id"] == item._button_id:
                    # Update the description label inside the collapsible
                    description_label = item.query_one(".info-text", Label)
                    description_label.update(self._get_setting_description(setting))
                    break

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
