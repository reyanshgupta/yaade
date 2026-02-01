#!/usr/bin/env bash
set -e

# AI Agent Configuration Setup Script
# Creates symlinks from project root to .agents/ configs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[SKIP]${NC} $1"; }

echo ""
echo "================================"
echo "  AI Agent Config Setup"
echo "================================"
echo ""

cd "$PROJECT_ROOT"

# Define symlinks: "source:target"
SYMLINKS=(
    ".agents/CLAUDE.md:CLAUDE.md"
    ".agents/.cursorrules:.cursorrules"
    ".agents/.aider.conf.yml:.aider.conf.yml"
)

for link in "${SYMLINKS[@]}"; do
    SOURCE="${link%%:*}"
    TARGET="${link##*:}"

    if [[ -L "$TARGET" ]]; then
        # Already a symlink
        warn "$TARGET (symlink exists)"
    elif [[ -f "$TARGET" ]]; then
        # File exists, not a symlink
        warn "$TARGET (file exists, skipping)"
    else
        ln -sf "$SOURCE" "$TARGET"
        success "$TARGET -> $SOURCE"
    fi
done

echo ""
info "Optional: For Continue, copy config manually:"
echo "    mkdir -p .continue && cp .agents/continue.json .continue/config.json"
echo ""
info "Optional: For other tools, create symlinks as needed:"
echo "    ln -sf .agents/OPENCODE.md OPENCODE.md"
echo "    ln -sf .agents/WINDSURF.md WINDSURF.md"
echo "    ln -sf .agents/ANTIGRAVITY.md ANTIGRAVITY.md"
echo ""
success "Setup complete!"
