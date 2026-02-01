#!/bin/bash
#
# Download embedding models for Yaade
# 
# Usage:
#   ./download-models.sh              # List available models
#   ./download-models.sh list         # List available models
#   ./download-models.sh all          # Download all models
#   ./download-models.sh <model_id>   # Download specific model
#   ./download-models.sh --help       # Show help
#

set -e

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║            Yaade Embedding Model Downloader                    ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_help() {
    print_header
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  list              List all available models and their cache status"
    echo "  all               Download all supported models"
    echo "  <model_id>        Download a specific model"
    echo "  check <model_id>  Check if a model is cached"
    echo ""
    echo "Options:"
    echo "  --force           Force re-download even if cached"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Available Models:"
    echo "  all-MiniLM-L6-v2          (~80 MB)   - Default, fast & efficient"
    echo "  all-MiniLM-L12-v2         (~120 MB)  - Better quality, still fast"
    echo "  all-mpnet-base-v2         (~420 MB)  - Highest quality, slower"
    echo "  paraphrase-MiniLM-L6-v2   (~80 MB)   - Good for paraphrase detection"
    echo "  multi-qa-MiniLM-L6-cos-v1 (~80 MB)   - Optimized for Q&A"
    echo "  bge-small-en-v1.5         (~130 MB)  - BAAI's efficient model"
    echo "  bge-base-en-v1.5          (~440 MB)  - Top-tier quality"
    echo ""
    echo "Examples:"
    echo "  $0 list                           # Show all models"
    echo "  $0 all-MiniLM-L6-v2               # Download default model"
    echo "  $0 all                            # Download all models"
    echo "  $0 all-mpnet-base-v2 --force      # Force re-download"
    echo ""
}

# Check if uv is available
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: uv not found in PATH.${NC}"
        echo "Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
}

# Run the yaade CLI command
run_yaade() {
    cd "$PROJECT_DIR"
    uv run yaade "$@"
}

# Main logic
main() {
    case "${1:-list}" in
        --help|-h)
            print_help
            exit 0
            ;;
        list)
            print_header
            check_uv
            echo -e "${YELLOW}Checking available models...${NC}\n"
            run_yaade download-model list
            ;;
        all)
            print_header
            check_uv
            echo -e "${YELLOW}Downloading all embedding models...${NC}"
            echo -e "${YELLOW}This may take a while depending on your connection.${NC}\n"
            if [ "$2" = "--force" ]; then
                run_yaade download-model all --force
            else
                run_yaade download-model all
            fi
            echo -e "\n${GREEN}Done!${NC}"
            ;;
        check)
            if [ -z "$2" ]; then
                echo -e "${RED}Error: model_id required for check command${NC}"
                echo "Usage: $0 check <model_id>"
                exit 1
            fi
            check_uv
            run_yaade download-model check "$2"
            ;;
        *)
            # Assume it's a model ID
            print_header
            check_uv
            MODEL_ID="$1"
            echo -e "${YELLOW}Downloading model: ${MODEL_ID}${NC}\n"
            if [ "$2" = "--force" ]; then
                run_yaade download-model download "$MODEL_ID" --force
            else
                run_yaade download-model download "$MODEL_ID"
            fi
            echo -e "\n${GREEN}Done!${NC}"
            ;;
    esac
}

main "$@"
