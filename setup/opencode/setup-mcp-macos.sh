#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_DIR="$HOME/.config/opencode"
CONFIG_FILE="$CONFIG_DIR/opencode.json"

echo "Setting up Yaade for OpenCode (macOS)"
echo "======================================"

# Detect: pip-installed yaade or run from repo with uv
YAADE_PATH=""
command -v yaade &> /dev/null && YAADE_PATH=$(which yaade)

if [[ -n "$YAADE_PATH" && "$YAADE_PATH" != "$PROJECT_ROOT/.venv/"* ]]; then
    USE_PIP_MODE=1
    echo "Using pip-installed yaade: $YAADE_PATH"
else
    if ! command -v uv &> /dev/null; then
        echo "Error: yaade not found in PATH and uv not installed."
        echo "  - Install yaade globally: pip install yaade"
        echo "  - Or install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    UV_PATH=$(which uv)
    USE_PIP_MODE=0
    echo "Using repo + uv (central directory: $PROJECT_ROOT)"
    cd "$PROJECT_ROOT"
    echo "Installing dependencies..."
    uv sync
fi

mkdir -p "$CONFIG_DIR"
[ -f "$CONFIG_FILE" ] && cp "$CONFIG_FILE" "$CONFIG_FILE.backup"

echo "Configuring MCP server..."

if [ "$USE_PIP_MODE" = "1" ]; then
    python3 "$PROJECT_ROOT/setup/mcp_config.py" write opencode "$CONFIG_FILE" 1 "$YAADE_PATH"
else
    python3 "$PROJECT_ROOT/setup/mcp_config.py" write opencode "$CONFIG_FILE" 0 "$UV_PATH" "$PROJECT_ROOT"
fi

echo "Setup complete!"
echo ""
echo "Configuration details:"
echo "   Config file: $CONFIG_FILE"
if [ "$USE_PIP_MODE" = "1" ]; then
    echo "   Mode: pip-installed yaade"
    echo "   Yaade path: $YAADE_PATH"
    echo ""
    echo "To test: yaade serve"
else
    echo "   Mode: run from repo (uv)"
    echo "   Project root: $PROJECT_ROOT"
    echo ""
    echo "To test: cd '$PROJECT_ROOT' && uv run yaade serve"
fi
echo ""
echo "Restart OpenCode to use Yaade."
