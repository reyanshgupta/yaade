"""CLI entry point for Yaade."""

# Set environment variables BEFORE any other imports to prevent
# PyTorch/tokenizers multiprocessing issues with Textual
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

import sys
import argparse


def main():
    """Main entry point for Yaade.
    
    Usage:
        yaade                    - Launch the TUI (default)
        yaade serve              - Run the MCP server (headless mode for Claude integration)
        yaade download-model     - Download embedding models
    """
    parser = argparse.ArgumentParser(
        prog="yaade",
        description="Yaade - Memory Storage for AI Agents"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Serve subcommand (for MCP server)
    subparsers.add_parser(
        "serve",
        help="Run the MCP server (headless mode for Claude integration)"
    )
    
    # Download model subcommand
    download_parser = subparsers.add_parser(
        "download-model",
        help="Download embedding models"
    )
    download_parser.add_argument(
        "model_action",
        nargs="?",
        choices=["list", "download", "check", "all"],
        default="list",
        help="Action to perform: list, download, check, or all (download all models)"
    )
    download_parser.add_argument(
        "model_id",
        nargs="?",
        help="Model ID for download/check commands (e.g., 'all-MiniLM-L6-v2')"
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if cached"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "serve":
            # Run MCP server (headless mode)
            from .main import main as serve_main
            serve_main()
        elif args.command == "download-model":
            # Model download commands
            from .search.model_downloader import (
                list_models, download_model, download_all_models, is_model_cached
            )
            
            if args.model_action == "list":
                list_models()
            elif args.model_action == "all":
                download_all_models(skip_cached=not args.force)
            elif args.model_action == "download":
                if args.model_id:
                    success = download_model(args.model_id, force=args.force)
                    if not success:
                        sys.exit(1)
                else:
                    download_all_models(skip_cached=not args.force)
            elif args.model_action == "check":
                if not args.model_id:
                    print("Error: model_id required for check command")
                    sys.exit(1)
                cached = is_model_cached(args.model_id)
                if cached:
                    print(f"✓ Model '{args.model_id}' is cached")
                else:
                    print(f"✗ Model '{args.model_id}' is not cached")
                    sys.exit(1)
        else:
            # Default: Launch TUI
            from .tui.app import run_tui
            run_tui()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
