"""CLI entry point for memory TUI."""

import sys


def main():
    """Main entry point for the TUI."""
    try:
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
