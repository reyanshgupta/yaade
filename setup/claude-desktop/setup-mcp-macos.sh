#!/bin/bash

echo "Setting up Claude Desktop MCP configuration for Yaade (macOS)..."

# Get the current project directory (absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv not found in PATH. Please install uv first."
    echo "You can install it from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Get full path to uv
UV_PATH=$(which uv)

# Claude Desktop config directory
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Create Claude config directory if it doesn't exist
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    mkdir -p "$CLAUDE_CONFIG_DIR"
    echo "Created Claude config directory: $CLAUDE_CONFIG_DIR"
fi

# Check if config file exists and back it up
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    echo "Backing up existing config to claude_desktop_config.json.backup"
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup"
fi

# Create or update the configuration
echo "Creating Claude Desktop MCP configuration..."

cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "yaade": {
      "command": "$UV_PATH",
      "args": ["run", "--directory", "$PROJECT_DIR", "yaade", "serve"],
      "env": {
        "YAADE_LOG_LEVEL": "INFO"
      }
    }
  }
}
EOF

echo
echo "Claude Desktop MCP configuration has been set up successfully!"
echo
echo "Configuration details:"
echo "- Project directory: $PROJECT_DIR"
echo "- UV path: $UV_PATH"
echo "- Config file: $CLAUDE_CONFIG_FILE"
echo
echo "Please restart Claude Desktop for the changes to take effect."
echo
