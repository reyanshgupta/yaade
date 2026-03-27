#!/usr/bin/env python3
"""Unified MCP configuration utility for Yaade setup scripts.

Usage:
    mcp_config.py read-env                    # Print env JSON to stdout
    mcp_config.py write <tool> <config_file> <use_pip> <command_path> [project_dir]

Tools: claude-code, claude-desktop, cursor, opencode

Examples:
    mcp_config.py read-env
    mcp_config.py write cursor ~/.cursor/mcp.json 1 /usr/local/bin/yaade
    mcp_config.py write claude-code ~/.claude.json 0 /usr/bin/uv /path/to/yaade
"""
import json
import os
import sys


def read_yaade_env() -> dict:
    """Read Yaade config from ~/.yaade/config.json and return env dict."""
    path = os.path.expanduser("~/.yaade/config.json")
    default_data = os.path.abspath(os.path.expanduser("~/.yaade"))
    env = {"YAADE_LOG_LEVEL": "INFO", "YAADE_DATA_DIR": default_data}
    if os.path.exists(path):
        try:
            with open(path) as f:
                c = json.load(f)
            if c.get("data_dir"):
                d = os.path.expanduser(str(c["data_dir"]))
                env["YAADE_DATA_DIR"] = os.path.abspath(d)
            if c.get("log_level"):
                env["YAADE_LOG_LEVEL"] = str(c["log_level"])
            if c.get("embedding_model_name"):
                env["YAADE_EMBEDDING_MODEL_NAME"] = str(c["embedding_model_name"])
        except Exception:
            pass
    return env


def build_entry(tool: str, use_pip: bool, command_path: str, project_dir: str, env: dict) -> dict:
    """Build the MCP server entry for a specific tool."""
    if use_pip:
        args = ["serve"]
        cmd = command_path
    else:
        args = ["run", "--directory", project_dir, "yaade", "serve"]
        cmd = command_path

    if tool == "claude-code":
        return {"type": "stdio", "command": cmd, "args": args, "env": env}
    elif tool == "claude-desktop":
        return {"command": cmd, "args": args, "env": env}
    elif tool == "cursor":
        return {"command": cmd, "args": args, "env": env}
    elif tool == "opencode":
        if use_pip:
            cmd_list = [command_path, "serve"]
        else:
            cmd_list = [command_path, "run", "--directory", project_dir, "yaade", "serve"]
        return {"type": "local", "command": cmd_list, "environment": env, "enabled": True}
    else:
        raise ValueError(f"Unknown tool: {tool}")


def write_config(tool: str, config_file: str, use_pip: bool, command_path: str, project_dir: str):
    """Write or merge MCP config for the specified tool."""
    env = read_yaade_env()
    entry = build_entry(tool, use_pip, command_path, project_dir, env)

    if tool == "claude-code":
        # Claude Code: merge into existing config, key is "yaade"
        config = {}
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
        config["yaade"] = entry
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    elif tool == "claude-desktop":
        # Claude Desktop: merge into mcpServers
        config = {}
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
        config.setdefault("mcpServers", {})["yaade"] = entry
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    elif tool == "cursor":
        # Cursor: merge into mcpServers
        config = {}
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
        config.setdefault("mcpServers", {})["yaade"] = entry
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    elif tool == "opencode":
        # OpenCode: merge into mcp section
        config = {"$schema": "https://opencode.ai/config.json", "mcp": {}}
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
            config.setdefault("mcp", {})
        config["mcp"]["yaade"] = entry
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "read-env":
        print(json.dumps(read_yaade_env()))

    elif command == "write":
        if len(sys.argv) < 6:
            print("Usage: mcp_config.py write <tool> <config_file> <use_pip> <command_path> [project_dir]")
            sys.exit(1)
        tool = sys.argv[2]
        config_file = sys.argv[3]
        use_pip = sys.argv[4] == "1"
        command_path = sys.argv[5]
        project_dir = sys.argv[6] if len(sys.argv) > 6 else ""
        write_config(tool, config_file, use_pip, command_path, project_dir)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
