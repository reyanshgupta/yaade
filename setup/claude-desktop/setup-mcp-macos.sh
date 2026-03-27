#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Setting up Yaade for Claude Desktop (macOS)"
echo "============================================"

# Detect: pip-installed yaade or run from repo with uv
YAADE_PATH=""
command -v yaade &> /dev/null && YAADE_PATH=$(which yaade)

if [[ -n "$YAADE_PATH" && "$YAADE_PATH" != "$PROJECT_DIR/.venv/"* ]]; then
    USE_PIP_MODE=1
    echo "Using pip-installed yaade: $YAADE_PATH"
else
    if ! command -v uv &> /dev/null; then
        echo "Error: yaade not found in PATH and uv not installed."
        echo "  - Install yaade globally: pip install yaade"
        echo "  - Or install uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    UV_PATH=$(which uv)
    USE_PIP_MODE=0
    echo "Using repo + uv (central directory: $PROJECT_DIR)"
fi

# Claude Desktop config
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

mkdir -p "$CLAUDE_CONFIG_DIR"
[ -f "$CLAUDE_CONFIG_FILE" ] && cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup"

echo "Configuring MCP server..."

if [ "$USE_PIP_MODE" = "1" ]; then
    python3 "$PROJECT_DIR/setup/mcp_config.py" write claude-desktop "$CLAUDE_CONFIG_FILE" 1 "$YAADE_PATH"
else
    python3 "$PROJECT_DIR/setup/mcp_config.py" write claude-desktop "$CLAUDE_CONFIG_FILE" 0 "$UV_PATH" "$PROJECT_DIR"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Configuration details:"
if [ "$USE_PIP_MODE" = "1" ]; then
    echo "   Mode: pip-installed yaade"
    echo "   Yaade path: $YAADE_PATH"
else
    echo "   Mode: run from repo (uv)"
    echo "   Project root: $PROJECT_DIR"
fi
echo "   Config file: $CLAUDE_CONFIG_FILE"
echo ""
echo "Restart Claude Desktop for changes to take effect."
