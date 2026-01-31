#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_DIR="$HOME/.config/opencode"
CONFIG_FILE="$CONFIG_DIR/opencode.json"

echo "Setting up Yaade for OpenCode (macOS)"
echo "======================================"

if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Please install UV first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "UV found"

cd "$PROJECT_ROOT"

echo "Installing dependencies..."
uv sync

echo "Creating OpenCode config directory..."
mkdir -p "$CONFIG_DIR"

echo "Configuring MCP server..."

# Check if config file exists and has mcp section
if [ -f "$CONFIG_FILE" ]; then
    echo "Existing config found, updating..."
    # Create a backup
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"

    # Check if mcp section exists
    if grep -q '"mcp"' "$CONFIG_FILE"; then
        # Add yaade to existing mcp section
        python3 -c "
import json
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)

    if 'mcp' not in config:
        config['mcp'] = {}

    config['mcp']['yaade'] = {
        'type': 'local',
        'command': ['uv', '--project', '$PROJECT_ROOT', 'run', 'yaade', 'serve'],
        'environment': {},
        'enabled': True
    }

    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)

    print('Updated existing config')
except Exception as e:
    print(f'Error updating config: {e}')
    sys.exit(1)
"
    else
        # Add mcp section to existing config
        python3 -c "
import json
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)

    config['mcp'] = {
        'yaade': {
            'type': 'local',
            'command': ['uv', '--project', '$PROJECT_ROOT', 'run', 'yaade', 'serve'],
            'environment': {},
            'enabled': True
        }
    }

    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)

    print('Added mcp section to existing config')
except Exception as e:
    print(f'Error updating config: {e}')
    sys.exit(1)
"
    fi
else
    echo "Creating new config file..."
    cat > "$CONFIG_FILE" << EOF
{
  "\$schema": "https://opencode.ai/config.json",
  "mcp": {
    "yaade": {
      "type": "local",
      "command": ["uv", "--project", "$PROJECT_ROOT", "run", "yaade", "serve"],
      "environment": {},
      "enabled": true
    }
  }
}
EOF
fi

echo "Setup complete!"
echo ""
echo "Configuration details:"
echo "   Config file: $CONFIG_FILE"
echo "   Project root: $PROJECT_ROOT"
echo ""
echo "To use Yaade:"
echo "   1. Restart OpenCode if it's running"
echo "   2. The MCP server will be available as 'yaade'"
echo "   3. Use tools like add_memory, search_memories, etc."
echo ""
echo "To test the server manually:"
echo "   cd '$PROJECT_ROOT' && uv run yaade serve"
