"""CLI entry point for Yaade."""

import sys
import argparse


def main():
    """Main entry point for Yaade.
    
    Usage:
        yaade          - Launch the TUI (default)
        yaade serve    - Run the MCP server (headless mode for Claude integration)
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
    
    args = parser.parse_args()
    
    try:
        if args.command == "serve":
            # Run MCP server (headless mode)
            from .main import main as serve_main
            serve_main()
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
