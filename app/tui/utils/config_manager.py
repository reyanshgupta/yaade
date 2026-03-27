"""Configuration manager for ~/.yaade/config.json (central config)."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from app.models.config import CENTRAL_CONFIG_PATH, YAADE_HOME

logger = logging.getLogger(__name__)

# Keys we persist in central config (same names as ServerConfig + TUI-only like theme)
CONFIG_KEYS = frozenset({
    "data_dir", "embedding_model_name", "embedding_batch_size", "embedding_max_seq_length",
    "host", "port", "log_level", "theme",
})


class ConfigManager:
    """Manages ~/.yaade/config.json as the single source of truth for user settings.

    All MCP clients (Claude Desktop, Cursor, etc.) and the TUI use this file.
    ServerConfig loads from it automatically; TUI reads/writes via these methods.
    """

    @staticmethod
    def get_config_path() -> Path:
        """Path to the central config file."""
        return CENTRAL_CONFIG_PATH

    @staticmethod
    def load_config() -> dict:
        """Read central config from ~/.yaade/config.json. Returns a dict; missing file => {}."""
        if not CENTRAL_CONFIG_PATH.exists():
            return {}
        try:
            with open(CENTRAL_CONFIG_PATH, "r") as f:
                data = json.load(f)
            return {k: v for k, v in data.items() if k in CONFIG_KEYS}
        except Exception as e:
            logger.warning("Failed to read %s: %s", CENTRAL_CONFIG_PATH, e)
            return {}

    @staticmethod
    def update_config(key: str, value: Any) -> bool:
        """Update one key in ~/.yaade/config.json. Creates ~/.yaade and file if needed."""
        if key not in CONFIG_KEYS:
            logger.warning("Unknown config key: %s", key)
            return False
        try:
            YAADE_HOME.mkdir(parents=True, exist_ok=True)
            data = ConfigManager.load_config()
            data[key] = str(value) if isinstance(value, Path) else value
            with open(CENTRAL_CONFIG_PATH, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.warning("Failed to update %s: %s", CENTRAL_CONFIG_PATH, e)
            return False

    @staticmethod
    def read_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
        """Read a config value from central config (kept for compatibility)."""
        data = ConfigManager.load_config()
        # Map legacy env names to config keys
        key_map = {"YAADE_DATA_DIR": "data_dir", "YAADE_THEME": "theme"}
        k = key_map.get(key, key.replace("YAADE_", "").lower())
        if k in data:
            return str(data[k])
        return default

    @staticmethod
    def update_env_variable(key: str, value: str) -> bool:
        """Update a config value in central config (kept for compatibility)."""
        key_map = {"YAADE_DATA_DIR": "data_dir", "YAADE_THEME": "theme"}
        k = key_map.get(key, key.replace("YAADE_", "").lower())
        return ConfigManager.update_config(k, value)

    @staticmethod
    def remove_env_variable(key: str) -> bool:
        """Remove a key from central config by setting it to empty (or we could delete the key)."""
        key_map = {"YAADE_DATA_DIR": "data_dir", "YAADE_THEME": "theme"}
        k = key_map.get(key, key.replace("YAADE_", "").lower())
        if k not in CONFIG_KEYS:
            return True
        try:
            data = ConfigManager.load_config()
            data.pop(k, None)
            if data:
                with open(CENTRAL_CONFIG_PATH, "w") as f:
                    json.dump(data, f, indent=2)
            elif CENTRAL_CONFIG_PATH.exists():
                CENTRAL_CONFIG_PATH.unlink()
            return True
        except Exception as e:
            logger.warning("Failed to remove %s from config: %s", key, e)
            return False
