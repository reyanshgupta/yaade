"""Unit tests for ConfigManager (central ~/.yaade/config.json)."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from app.tui.utils.config_manager import ConfigManager, CONFIG_KEYS


@pytest.fixture
def central_config_path(temp_dir):
    """Use a temp dir as YAADE_HOME and return path to config.json."""
    config_path = temp_dir / "config.json"
    with patch("app.tui.utils.config_manager.YAADE_HOME", temp_dir), patch(
        "app.tui.utils.config_manager.CENTRAL_CONFIG_PATH", config_path
    ):
        yield config_path


class TestConfigManager:
    """Tests for ConfigManager (central config at ~/.yaade/config.json)."""

    def test_get_config_path(self):
        """Test getting the central config file path."""
        result = ConfigManager.get_config_path()
        assert result.name == "config.json"
        assert ".yaade" in str(result)

    def test_load_config_missing_file(self, central_config_path):
        """Test loading when config file doesn't exist."""
        assert not central_config_path.exists()
        result = ConfigManager.load_config()
        assert result == {}

    def test_load_config_returns_only_known_keys(self, central_config_path):
        """Test that load_config filters to CONFIG_KEYS only."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        central_config_path.write_text(
            json.dumps({"data_dir": "~/.yaade", "theme": "cyberpunk", "unknown_key": "ignored"})
        )
        result = ConfigManager.load_config()
        assert "data_dir" in result
        assert "theme" in result
        assert "unknown_key" not in result

    def test_update_config_creates_file_and_dir(self, central_config_path):
        """Test that update_config creates ~/.yaade and config.json."""
        assert not central_config_path.exists()
        result = ConfigManager.update_config("data_dir", "~/.yaade")
        assert result is True
        assert central_config_path.exists()
        data = json.loads(central_config_path.read_text())
        assert data["data_dir"] == "~/.yaade"

    def test_update_config_merges_with_existing(self, central_config_path):
        """Test that update_config merges with existing config."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        central_config_path.write_text(json.dumps({"theme": "cyberpunk"}))
        ConfigManager.update_config("data_dir", "/custom/path")
        data = json.loads(central_config_path.read_text())
        assert data["theme"] == "cyberpunk"
        assert data["data_dir"] == "/custom/path"

    def test_read_env_variable_legacy_yaade_data_dir(self, central_config_path):
        """Test read_env_variable('YAADE_DATA_DIR') reads data_dir from config."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        central_config_path.write_text(json.dumps({"data_dir": "/my/storage"}))
        result = ConfigManager.read_env_variable("YAADE_DATA_DIR")
        assert result == "/my/storage"

    def test_read_env_variable_legacy_yaade_theme(self, central_config_path):
        """Test read_env_variable('YAADE_THEME') reads theme from config."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        central_config_path.write_text(json.dumps({"theme": "neon_nights"}))
        result = ConfigManager.read_env_variable("YAADE_THEME")
        assert result == "neon_nights"

    def test_read_env_variable_returns_default_when_missing(self, central_config_path):
        """Test read_env_variable returns default when key not in config."""
        result = ConfigManager.read_env_variable("YAADE_DATA_DIR", "default_value")
        assert result == "default_value"

    def test_update_env_variable_yaade_data_dir(self, central_config_path):
        """Test update_env_variable('YAADE_DATA_DIR') writes data_dir to config."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        result = ConfigManager.update_env_variable("YAADE_DATA_DIR", "/new/path")
        assert result is True
        data = json.loads(central_config_path.read_text())
        assert data["data_dir"] == "/new/path"

    def test_update_env_variable_yaade_theme(self, central_config_path):
        """Test update_env_variable('YAADE_THEME') writes theme to config."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        result = ConfigManager.update_env_variable("YAADE_THEME", "cyberpunk")
        assert result is True
        data = json.loads(central_config_path.read_text())
        assert data["theme"] == "cyberpunk"

    def test_update_config_rejects_unknown_key(self, central_config_path):
        """Test update_config returns False for unknown key."""
        result = ConfigManager.update_config("unknown_key", "value")
        assert result is False

    def test_remove_env_variable_removes_key(self, central_config_path):
        """Test remove_env_variable removes the key from config."""
        central_config_path.parent.mkdir(parents=True, exist_ok=True)
        central_config_path.write_text(json.dumps({"data_dir": "~/.yaade", "theme": "cyberpunk"}))
        result = ConfigManager.remove_env_variable("YAADE_DATA_DIR")
        assert result is True
        data = json.loads(central_config_path.read_text())
        assert "data_dir" not in data
        assert data["theme"] == "cyberpunk"

    def test_remove_env_variable_file_not_exists(self, central_config_path):
        """Test remove when config file doesn't exist."""
        result = ConfigManager.remove_env_variable("YAADE_DATA_DIR")
        assert result is True
