#!/bin/bash

# Install Yaade Claude Code skills globally so /remember, /recall, etc.
# are available in every Claude Code session, not just the yaade project.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILLS_SRC="$PROJECT_ROOT/.claude/commands"
SKILLS_DST="$HOME/.claude/commands"

echo "Installing Yaade Claude Code skills"
echo "====================================="
echo "Source : $SKILLS_SRC"
echo "Target : $SKILLS_DST"
echo ""

# Validate source directory
if [ ! -d "$SKILLS_SRC" ]; then
    echo "Error: Skills directory not found at $SKILLS_SRC"
    exit 1
fi

# Create destination if it doesn't exist
mkdir -p "$SKILLS_DST"

# Copy each skill file, warn if overwriting
INSTALLED=0
SKIPPED=0

for skill_file in "$SKILLS_SRC"/*.md; do
    [ -f "$skill_file" ] || continue
    skill_name="$(basename "$skill_file")"
    dest="$SKILLS_DST/$skill_name"

    if [ -f "$dest" ]; then
        echo "  [overwrite] $skill_name"
    else
        echo "  [install]   $skill_name"
    fi

    cp "$skill_file" "$dest"
    INSTALLED=$((INSTALLED + 1))
done

echo ""
echo "Installed $INSTALLED skill(s) to $SKILLS_DST"
echo ""
echo "Available slash commands in Claude Code:"
echo "   /remember <content>   — Store a memory"
echo "   /recall <query>       — Search memories semantically"
echo "   /forget <id or desc>  — Delete a memory"
echo "   /memory-status        — Check Yaade server health"
echo "   /memory-cleanup       — Find and remove duplicate memories"
echo ""
echo "Note: Yaade's MCP server must also be configured for these to work."
echo "If you haven't done that yet, run:"
echo ""

# Detect OS and suggest the right setup script
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   ./setup/claude-code/setup-mcp-macos.sh"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "   .\\setup\\claude-code\\setup-mcp-windows.bat"
else
    echo "   ./setup/claude-code/setup-mcp-linux.sh"
fi

echo ""
echo "Then restart Claude Code."
