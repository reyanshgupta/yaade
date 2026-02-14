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
from .settings import OnboardingScreen, SetupScreen, SettingsScreen
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
            manager: Pre-initialized MemoryManager, or None on first run (manager
                    is created after onboarding completes).
        """
        super().__init__()
        self.is_first_run = self._check_first_run()
        # Manager may be None on first run until onboarding completes
        self.manager = manager
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
            config_data = self._get_config_data()
            self.push_screen(OnboardingScreen(config_data), self._handle_first_run_complete)
        else:
            # Already set up: go directly to memory management with menu in background
            self.push_screen("menu")
            self.push_screen("memory_screen")

    def _get_config_data(self) -> dict:
        """Get configuration data for settings screen."""
        if self.manager is not None:
            c = self.manager.config
        else:
            from ..models.config import ServerConfig
            c = ServerConfig()
        return {
            'data_dir': str(c.data_dir),
            'embedding_model': c.embedding_model_name,
            'host': c.host,
            'port': c.port,
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
        """Check if this is the first run (chroma store not yet created or empty).

        Setup is complete only when the chroma path exists and contains files
        (actual ChromaDB data). An empty or partially-initialized chroma dir
        is treated as first run so we show onboarding and avoid loading from
        an incomplete database.

        Returns:
            True if first run (needs setup), False if already configured
        """
        from ..models.config import ServerConfig

        config = ServerConfig()
        chroma_path = config.chroma_path
        if not chroma_path.exists():
            return True  # No chroma dir → first run
        try:
            # Must have at least one real file (not just .DS_Store etc.)
            files = [f for f in chroma_path.iterdir() if not f.name.startswith('.')]
            return not files  # Empty or only dotfiles → first run
        except Exception:
            return True  # Can't read dir → treat as first run

    def _handle_first_run_complete(self, result: Optional[bool]) -> None:
        """Handle completion of first-time setup.

        Args:
            result: True if setup completed, False/None if cancelled
        """
        if result:
            # Create manager now (reads .env, creates .yaade in chosen path)
            global _global_manager
            _global_manager = _init_manager()
            self.manager = _global_manager
            self.push_screen("menu")
            self.push_screen("memory_screen")
        else:
            self.exit()


def run_tui() -> None:
    """Run the TUI application."""
    # Check first run BEFORE creating MemoryManager (which creates .yaade and chroma)
    is_first_run = Yaade._check_first_run()
    if is_first_run:
        # Onboarding: show setup first; manager is created after user continues
        app = Yaade(manager=None)
    else:
        # Already set up: init manager before Textual to avoid PyTorch fd issues
        manager = _init_manager()
        app = Yaade(manager=manager)
    app.run()
