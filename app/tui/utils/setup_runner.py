"""Setup script runner for MCP integration."""

import platform
import subprocess
from pathlib import Path
from typing import Tuple
from dataclasses import dataclass


@dataclass
class SetupResult:
    """Result of a setup script execution."""
    output: str
    success: bool
    error: str = ""


class SetupRunner:
    """Runs MCP setup scripts for Claude Desktop/Code.
    
    This class centralizes setup script execution to avoid code duplication
    between the setup handlers for different Claude clients.
    """

    # Supported client types and their script directories
    CLIENT_TYPES = {
        "claude-desktop": "claude-desktop",
        "claude-code": "claude-code",
        "opencode": "opencode",
    }

    @staticmethod
    def get_os_type() -> str:
        """Get the current operating system type.
        
        Returns:
            'Darwin' for macOS, 'Windows' for Windows, or the raw platform.system() value.
        """
        return platform.system()

    @staticmethod
    def get_script_path(client_type: str) -> Path:
        """Get the path to the setup script for the given client type.
        
        Args:
            client_type: Either 'claude-desktop' or 'claude-code'.
            
        Returns:
            Path to the setup script.
            
        Raises:
            ValueError: If client_type is not supported.
        """
        if client_type not in SetupRunner.CLIENT_TYPES:
            raise ValueError(f"Unsupported client type: {client_type}. "
                           f"Supported types: {list(SetupRunner.CLIENT_TYPES.keys())}")
        
        os_type = SetupRunner.get_os_type()
        script_dir = SetupRunner.CLIENT_TYPES[client_type]
        
        if os_type == "Darwin":  # macOS
            script_name = "setup-mcp-macos.sh"
        elif os_type == "Windows":
            script_name = "setup-mcp-windows.bat"
        else:
            raise ValueError(f"Unsupported OS for automatic setup: {os_type}")
        
        return Path.cwd() / "setup" / script_dir / script_name

    @staticmethod
    def run_setup(client_type: str, timeout: int = 30) -> SetupResult:
        """Run the setup script for the specified client.
        
        Args:
            client_type: Either 'claude-desktop' or 'claude-code'.
            timeout: Maximum time in seconds to wait for the script.
            
        Returns:
            SetupResult with output, success status, and any error message.
        """
        try:
            script_path = SetupRunner.get_script_path(client_type)
        except ValueError as e:
            return SetupResult(output="", success=False, error=str(e))
        
        if not script_path.exists():
            return SetupResult(
                output="",
                success=False,
                error=f"Setup script not found: {script_path}"
            )
        
        os_type = SetupRunner.get_os_type()
        
        try:
            if os_type == "Darwin":
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:  # Windows
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True
                )
            
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            
            return SetupResult(
                output=output.strip(),
                success=result.returncode == 0
            )
            
        except subprocess.TimeoutExpired:
            return SetupResult(
                output="",
                success=False,
                error="Setup script timed out"
            )
        except Exception as e:
            return SetupResult(
                output="",
                success=False,
                error=f"Setup failed: {str(e)}"
            )

    @staticmethod
    def get_client_display_name(client_type: str) -> str:
        """Get a human-readable display name for the client type.
        
        Args:
            client_type: Either 'claude-desktop' or 'claude-code'.
            
        Returns:
            Display name like 'Claude Desktop' or 'Claude Code'.
        """
        names = {
            "claude-desktop": "Claude Desktop",
            "claude-code": "Claude Code",
            "opencode": "OpenCode",
        }
        return names.get(client_type, client_type)
