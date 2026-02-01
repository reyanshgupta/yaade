"""Main Textual TUI application for memory management."""

# Set environment variables BEFORE importing torch/transformers to avoid
# file descriptor issues with Textual's event loop
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from pathlib import Path
from typing import Optional

from textual.app import App
from textual.binding import Binding

from .memory_manager import MemoryManager
from .screens import MainMenuScreen, MemoryManagementScreen
from .screens.modals import ThemeSelectScreen
from .settings import SetupScreen, SettingsScreen
from .themes import CUSTOM_THEMES
from .utils import ConfigManager


# Global manager instance - initialized before Textual to avoid file descriptor issues
_global_manager: Optional[MemoryManager] = None


def _init_manager() -> MemoryManager:
    """Initialize and preload the memory manager before Textual starts.

    This must be called before creating the Yaade app to avoid PyTorch
    file descriptor conflicts with Textual's event loop.
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = MemoryManager()
        # Preload the model NOW, before Textual starts
        try:
            _global_manager.embedding_service._ensure_model_loaded()
            # Do a test encoding to ensure everything is fully initialized
            _global_manager.embedding_service._encode_sync("warmup")
        except Exception:
            pass  # Model will try to load on first use
    return _global_manager


class Yaade(App):
    """A Textual TUI for memory management."""

    TITLE = "yaade"
    ENABLE_COMMAND_PALETTE = False  # Disable built-in command palette

    BINDINGS = [
        Binding("ctrl+p", "open_theme_selector", "Themes", show=False),
    ]

    CSS_PATH = [
        Path(__file__).parent / "styles" / "app.tcss",
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

    /* Let Textual handle button styling with defaults */

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

    def __init__(self, manager: Optional[MemoryManager] = None):
        """Initialize the TUI.

        Args:
            manager: Pre-initialized MemoryManager (recommended to avoid
                    PyTorch file descriptor issues with Textual)
        """
        super().__init__()
        # Check first run BEFORE creating MemoryManager (which creates directories)
        self.is_first_run = self._check_first_run()
        # Use provided manager or get from global (initialized before Textual)
        self.manager = manager if manager is not None else _init_manager()
        # Load saved theme
        self._saved_theme = self._load_theme()

    @staticmethod
    def _load_theme() -> str:
        """Load theme from .env file.

        Returns:
            Theme name, defaults to 'cyberpunk'
        """
        # Try new variable name first, then legacy
        theme = ConfigManager.read_env_variable("YAADE_THEME")
        if theme:
            return theme
        
        theme = ConfigManager.read_env_variable("MEMORY_SERVER_THEME")
        if theme:
            return theme
            
        return 'cyberpunk'  # Default to cyberpunk theme

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Register custom themes
        for theme in CUSTOM_THEMES:
            self.register_theme(theme)

        # Apply saved theme
        self.theme = self._saved_theme

        if self.is_first_run:
            # First-time setup: show setup screen directly
            config_data = self._get_config_data()
            self.push_screen(SetupScreen(config_data, is_first_run=True), self._handle_first_run_complete)
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
        """Save theme to .env file using ConfigManager."""
        success = ConfigManager.update_env_variable("YAADE_THEME", theme)
        if success:
            self.notify(f"Theme changed to: {theme}", severity="information")
        else:
            self.notify("Failed to save theme preference", severity="error")

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
    # Initialize and preload the manager BEFORE creating the Textual app
    # This avoids PyTorch file descriptor conflicts with Textual's event loop
    manager = _init_manager()
    app = Yaade(manager=manager)
    app.run()
