"""Unit tests for ConfigManager (TUI utilities)."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from app.tui.utils.config_manager import ConfigManager


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_get_env_path(self):
        """Test getting the .env file path."""
        with patch('app.tui.utils.config_manager.Path.cwd', return_value=Path('/test/path')):
            result = ConfigManager.get_env_path()
            assert result == Path('/test/path/.env')

    def test_read_env_variable_file_not_exists(self, temp_dir):
        """Test reading variable when .env file doesn't exist."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_dir / '.env'):
            result = ConfigManager.read_env_variable('TEST_VAR')
            assert result is None

    def test_read_env_variable_file_not_exists_with_default(self, temp_dir):
        """Test reading variable returns default when file doesn't exist."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_dir / '.env'):
            result = ConfigManager.read_env_variable('TEST_VAR', 'default_value')
            assert result == 'default_value'

    def test_read_env_variable_found(self, temp_env_file):
        """Test reading an existing variable."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.read_env_variable('EXISTING_VAR')
            assert result == 'existing_value'

    def test_read_env_variable_not_found(self, temp_env_file):
        """Test reading a non-existent variable."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.read_env_variable('NONEXISTENT_VAR')
            assert result is None

    def test_read_env_variable_not_found_with_default(self, temp_env_file):
        """Test reading non-existent variable returns default."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.read_env_variable('NONEXISTENT_VAR', 'fallback')
            assert result == 'fallback'

    def test_read_env_variable_handles_equals_in_value(self, temp_dir):
        """Test reading variable with equals sign in value."""
        env_path = temp_dir / '.env'
        env_path.write_text('URL=http://example.com?key=value&other=123\n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.read_env_variable('URL')
            assert result == 'http://example.com?key=value&other=123'

    def test_update_env_variable_new_file(self, temp_dir):
        """Test updating variable creates new .env file."""
        env_path = temp_dir / '.env'
        assert not env_path.exists()
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.update_env_variable('NEW_VAR', 'new_value')
            
            assert result is True
            assert env_path.exists()
            assert 'NEW_VAR=new_value' in env_path.read_text()

    def test_update_env_variable_existing_variable(self, temp_env_file):
        """Test updating an existing variable."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.update_env_variable('EXISTING_VAR', 'updated_value')
            
            assert result is True
            content = temp_env_file.read_text()
            assert 'EXISTING_VAR=updated_value' in content
            assert 'EXISTING_VAR=existing_value' not in content

    def test_update_env_variable_add_new(self, temp_env_file):
        """Test adding a new variable to existing file."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.update_env_variable('BRAND_NEW_VAR', 'brand_new_value')
            
            assert result is True
            content = temp_env_file.read_text()
            assert 'BRAND_NEW_VAR=brand_new_value' in content
            # Existing vars should still be there
            assert 'EXISTING_VAR=existing_value' in content
            assert 'ANOTHER_VAR=another_value' in content

    def test_update_env_variable_preserves_order(self, temp_dir):
        """Test that updating preserves variable order."""
        env_path = temp_dir / '.env'
        env_path.write_text('FIRST=1\nSECOND=2\nTHIRD=3\n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            ConfigManager.update_env_variable('SECOND', 'updated')
            
            lines = env_path.read_text().strip().split('\n')
            assert lines[0] == 'FIRST=1'
            assert lines[1] == 'SECOND=updated'
            assert lines[2] == 'THIRD=3'

    def test_update_env_variable_adds_newline_if_missing(self, temp_dir):
        """Test that updating adds newline if file doesn't end with one."""
        env_path = temp_dir / '.env'
        env_path.write_text('EXISTING=value')  # No trailing newline
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            ConfigManager.update_env_variable('NEW_VAR', 'new_value')
            
            content = env_path.read_text()
            # Should have proper newlines
            assert content.count('\n') >= 2

    def test_remove_env_variable_file_not_exists(self, temp_dir):
        """Test removing variable when file doesn't exist."""
        env_path = temp_dir / '.env'
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.remove_env_variable('SOME_VAR')
            # Should succeed (nothing to remove)
            assert result is True

    def test_remove_env_variable_success(self, temp_env_file):
        """Test removing an existing variable."""
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.remove_env_variable('EXISTING_VAR')
            
            assert result is True
            content = temp_env_file.read_text()
            assert 'EXISTING_VAR' not in content
            # Other vars should remain
            assert 'ANOTHER_VAR=another_value' in content

    def test_remove_env_variable_not_found(self, temp_env_file):
        """Test removing a non-existent variable."""
        original_content = temp_env_file.read_text()
        
        with patch.object(ConfigManager, 'get_env_path', return_value=temp_env_file):
            result = ConfigManager.remove_env_variable('NONEXISTENT_VAR')
            
            assert result is True
            # Content should be unchanged
            assert temp_env_file.read_text() == original_content

    def test_remove_env_variable_partial_match_not_removed(self, temp_dir):
        """Test that partial key matches are not removed."""
        env_path = temp_dir / '.env'
        env_path.write_text('MY_VAR=value\nMY_VAR_EXTENDED=extended\n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            ConfigManager.remove_env_variable('MY_VAR')
            
            content = env_path.read_text()
            assert 'MY_VAR_EXTENDED=extended' in content
            assert 'MY_VAR=value' not in content

    def test_read_env_variable_exception_handling(self, temp_dir):
        """Test that read handles exceptions gracefully."""
        env_path = temp_dir / '.env'
        env_path.write_text('TEST=value\n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                result = ConfigManager.read_env_variable('TEST', 'default')
                assert result == 'default'

    def test_update_env_variable_exception_handling(self, temp_dir):
        """Test that update handles exceptions gracefully."""
        env_path = temp_dir / '.env'
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            # Simulate write error
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                result = ConfigManager.update_env_variable('TEST', 'value')
                assert result is False

    def test_remove_env_variable_exception_handling(self, temp_dir):
        """Test that remove handles exceptions gracefully."""
        env_path = temp_dir / '.env'
        env_path.write_text('TEST=value\n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                result = ConfigManager.remove_env_variable('TEST')
                assert result is False

    def test_read_env_variable_empty_file(self, temp_dir):
        """Test reading from empty .env file."""
        env_path = temp_dir / '.env'
        env_path.write_text('')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.read_env_variable('ANY_VAR')
            assert result is None

    def test_read_env_variable_whitespace_handling(self, temp_dir):
        """Test reading handles whitespace lines."""
        env_path = temp_dir / '.env'
        env_path.write_text('\n  \nTEST=value\n  \n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.read_env_variable('TEST')
            assert result == 'value'

    def test_update_env_variable_empty_value(self, temp_dir):
        """Test updating with empty value."""
        env_path = temp_dir / '.env'
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.update_env_variable('EMPTY_VAR', '')
            
            assert result is True
            content = env_path.read_text()
            assert 'EMPTY_VAR=' in content

    def test_read_env_variable_comment_lines(self, temp_dir):
        """Test that comment lines don't interfere with reading."""
        env_path = temp_dir / '.env'
        env_path.write_text('# This is a comment\nTEST=value\n#COMMENTED=out\n')
        
        with patch.object(ConfigManager, 'get_env_path', return_value=env_path):
            result = ConfigManager.read_env_variable('TEST')
            assert result == 'value'
            
            # Commented variable should not be read
            result_commented = ConfigManager.read_env_variable('COMMENTED')
            assert result_commented is None
