"""Configuration manager for .env file operations."""

from pathlib import Path
from typing import Optional


class ConfigManager:
    """Manages .env file operations for TUI settings.
    
    This class centralizes all .env file manipulation to avoid code duplication
    across different TUI screens (settings, setup, theme selection, etc.).
    """

    @staticmethod
    def get_env_path() -> Path:
        """Get the path to the .env file.
        
        Returns:
            Path to the .env file in the current working directory.
        """
        return Path.cwd() / '.env'

    @staticmethod
    def read_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
        """Read an environment variable from .env file.
        
        Args:
            key: The environment variable name to read.
            default: Default value if the variable is not found.
            
        Returns:
            The variable value or default if not found.
        """
        env_path = ConfigManager.get_env_path()
        if not env_path.exists():
            return default
            
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{key}='):
                        return line.split('=', 1)[1]
        except Exception:
            pass
            
        return default

    @staticmethod
    def update_env_variable(key: str, value: str) -> bool:
        """Update or add an environment variable in .env file.
        
        This method handles both updating existing variables and adding new ones.
        It preserves the order and formatting of other variables in the file.
        
        Args:
            key: The environment variable name to update.
            value: The new value to set.
            
        Returns:
            True if successful, False otherwise.
        """
        env_path = ConfigManager.get_env_path()
        
        try:
            # Read existing .env or start with empty list
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()

            # Update or add the variable
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith(f'{key}='):
                    env_lines[i] = f'{key}={value}\n'
                    found = True
                    break

            if not found:
                # Add newline if file doesn't end with one
                if env_lines and not env_lines[-1].endswith('\n'):
                    env_lines[-1] += '\n'
                env_lines.append(f'{key}={value}\n')

            # Write back
            with open(env_path, 'w') as f:
                f.writelines(env_lines)

            return True
            
        except Exception:
            return False

    @staticmethod
    def remove_env_variable(key: str) -> bool:
        """Remove an environment variable from .env file.
        
        Args:
            key: The environment variable name to remove.
            
        Returns:
            True if successful (or variable didn't exist), False on error.
        """
        env_path = ConfigManager.get_env_path()
        
        if not env_path.exists():
            return True
            
        try:
            with open(env_path, 'r') as f:
                env_lines = f.readlines()

            # Filter out the variable
            new_lines = [line for line in env_lines if not line.startswith(f'{key}=')]

            with open(env_path, 'w') as f:
                f.writelines(new_lines)

            return True
            
        except Exception:
            return False
