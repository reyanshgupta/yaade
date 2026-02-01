#!/usr/bin/env bash
set -e

# Yaade CLI Uninstaller

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Find and remove wrapper script
remove_wrapper() {
    LOCATIONS=(
        "$HOME/.local/bin/yaade"
        "/usr/local/bin/yaade"
        "${YAADE_INSTALL_DIR}/yaade"
    )

    REMOVED=false
    for loc in "${LOCATIONS[@]}"; do
        if [[ -f "$loc" ]]; then
            info "Removing $loc..."
            rm -f "$loc"
            success "Removed $loc"
            REMOVED=true
        fi
    done

    if [[ "$REMOVED" == false ]]; then
        warn "No yaade wrapper found in standard locations"
    fi
}

# Main
main() {
    echo ""
    echo "======================================"
    echo "      Yaade CLI Uninstaller"
    echo "======================================"
    echo ""

    remove_wrapper

    echo ""
    warn "Note: This uninstaller removes the CLI wrapper only."
    warn "To fully remove yaade:"
    echo "  1. Delete the project directory"
    echo "  2. Remove ~/.yaade/ for data cleanup (if desired)"
    echo "  3. Remove PATH entry from your shell config (if added)"
    echo ""
    success "Uninstall complete!"
    echo ""
}

main "$@"
