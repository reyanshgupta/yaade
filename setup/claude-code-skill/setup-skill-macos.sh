#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/yaade"

echo "Setting up Yaade skill for Claude Code (macOS/Linux)"
echo "====================================================="

# Create skill directory
mkdir -p "$SKILL_DIR"

# Copy skill file
cp "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/SKILL.md"

echo "Setup complete!"
echo ""
echo "Skill installed to: $SKILL_DIR"
echo ""
echo "Usage:"
echo "  - Type /yaade to invoke the skill"
echo "  - Or say 'remember this' / 'what do you remember about'"
echo ""
echo "Note: Make sure the Yaade MCP server is configured and running."
echo "      Run: yaade serve"
