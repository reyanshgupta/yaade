"""Unit tests for ServerConfig model."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from app.models.config import ServerConfig


class TestServerConfig:
    """Tests for ServerConfig model."""

    def test_config_default_values(self):
        """Test ServerConfig has correct default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = ServerConfig()
            
            assert config.data_dir == Path(".yaade")
            assert config.embedding_model_name == "all-MiniLM-L6-v2"
            assert config.embedding_batch_size == 32
            assert config.embedding_max_seq_length == 512
            assert config.host == "localhost"
            assert config.port == 8000
            assert config.log_level == "INFO"

    def test_config_chroma_path_property(self):
        """Test chroma_path computed property."""
        config = ServerConfig()
        expected = config.data_dir / "chroma"
        assert config.chroma_path == expected

    def test_config_sqlite_path_property(self):
        """Test sqlite_path computed property."""
        config = ServerConfig()
        expected = config.data_dir / "metadata.db"
        assert config.sqlite_path == expected

    def test_config_custom_data_dir(self):
        """Test ServerConfig with custom data directory."""
        with patch.dict(os.environ, {"YAADE_DATA_DIR": "/custom/path"}, clear=True):
            config = ServerConfig()
            assert config.data_dir == Path("/custom/path")
            assert config.chroma_path == Path("/custom/path/chroma")
            assert config.sqlite_path == Path("/custom/path/metadata.db")

    def test_config_env_prefix(self):
        """Test that environment variables use YAADE_ prefix."""
        with patch.dict(os.environ, {
            "YAADE_HOST": "0.0.0.0",
            "YAADE_PORT": "9000",
            "YAADE_LOG_LEVEL": "DEBUG"
        }, clear=True):
            config = ServerConfig()
            assert config.host == "0.0.0.0"
            assert config.port == 9000
            assert config.log_level == "DEBUG"

    def test_config_embedding_settings(self):
        """Test custom embedding settings from environment."""
        with patch.dict(os.environ, {
            "YAADE_EMBEDDING_MODEL_NAME": "custom-model",
            "YAADE_EMBEDDING_BATCH_SIZE": "64",
            "YAADE_EMBEDDING_MAX_SEQ_LENGTH": "1024"
        }, clear=True):
            config = ServerConfig()
            assert config.embedding_model_name == "custom-model"
            assert config.embedding_batch_size == 64
            assert config.embedding_max_seq_length == 1024

    def test_config_ignores_unknown_env_vars(self):
        """Test that extra environment variables are ignored."""
        with patch.dict(os.environ, {
            "YAADE_UNKNOWN_VAR": "some_value",
            "YAADE_ANOTHER_UNKNOWN": "another_value"
        }, clear=True):
            # Should not raise an error
            config = ServerConfig()
            assert not hasattr(config, "unknown_var")
            assert not hasattr(config, "another_unknown")

    def test_config_path_types(self):
        """Test that path properties return Path objects."""
        config = ServerConfig()
        assert isinstance(config.data_dir, Path)
        assert isinstance(config.chroma_path, Path)
        assert isinstance(config.sqlite_path, Path)

    def test_config_port_is_integer(self):
        """Test that port is correctly parsed as integer."""
        with patch.dict(os.environ, {"YAADE_PORT": "8080"}, clear=True):
            config = ServerConfig()
            assert config.port == 8080
            assert isinstance(config.port, int)

    def test_config_batch_size_is_integer(self):
        """Test that embedding_batch_size is correctly parsed as integer."""
        with patch.dict(os.environ, {"YAADE_EMBEDDING_BATCH_SIZE": "128"}, clear=True):
            config = ServerConfig()
            assert config.embedding_batch_size == 128
            assert isinstance(config.embedding_batch_size, int)

    def test_config_relative_and_absolute_paths(self):
        """Test both relative and absolute data_dir paths."""
        # Relative path
        with patch.dict(os.environ, {"YAADE_DATA_DIR": "relative/path"}, clear=True):
            config = ServerConfig()
            assert config.data_dir == Path("relative/path")
        
        # Absolute path
        with patch.dict(os.environ, {"YAADE_DATA_DIR": "/absolute/path"}, clear=True):
            config = ServerConfig()
            assert config.data_dir == Path("/absolute/path")
            assert config.data_dir.is_absolute()

    def test_config_log_level_values(self):
        """Test various log level values."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            with patch.dict(os.environ, {"YAADE_LOG_LEVEL": level}, clear=True):
                config = ServerConfig()
                assert config.log_level == level
