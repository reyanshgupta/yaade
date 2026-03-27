# Yaade Skill for Claude Code

Persistent semantic memory for Claude Code conversations.

## Installation

Run the setup script for your platform:

**macOS/Linux:**
```bash
./setup/claude-code-skill/setup-skill-macos.sh
```

**Windows:**
```batch
setup\claude-code-skill\setup-skill-windows.bat
```

Or manually:
```bash
mkdir -p ~/.claude/skills/yaade
cp setup/claude-code-skill/SKILL.md ~/.claude/skills/yaade/
```

## Requirements

- Yaade MCP server configured in Claude Code
- Server running: `yaade serve`

## Usage

- `/yaade` - Invoke the skill
- "Remember that I prefer dark mode" - Auto-invoked
- "What do you remember about my preferences?" - Auto-invoked

## Operations

- **Store**: "remember this", "save for later"
- **Search**: "what do you remember about", "find memories"
- **Manage**: "delete that memory", "clean up duplicates"
- **Status**: "check memory status"

## MCP Tools Referenced

| Tool | Purpose |
|------|---------|
| `mcp__yaade__health_check` | Server status, memory count |
| `mcp__yaade__add_memory` | Store memory (content, type, source, tags, importance) |
| `mcp__yaade__search_memories` | Semantic search (query, limit, filter_tags) |
| `mcp__yaade__get_memory` | Retrieve by ID |
| `mcp__yaade__delete_memory` | Delete by ID |
| `mcp__yaade__analyze_memory_cleanup` | Find duplicates |
| `mcp__yaade__execute_memory_cleanup` | Execute cleanup (requires confirm_deletion=True) |

## Key Design Decisions

1. **ToolSearch required first** - MCP tools are deferred and must be loaded before use
2. **Source always "claude"** - Identifies memories stored by Claude Code
3. **Confirm before deletion** - Always ask user before destructive operations
4. **Context-rich memories** - Guide Claude to store self-contained, useful content
5. **No secrets** - Never store passwords, API keys, or sensitive data

## Verification

1. Run the setup script for your platform
2. Run `/yaade` in Claude Code to verify skill loads
3. Test operations:
   - Health check: "check memory status"
   - Store: "remember that I prefer TypeScript"
   - Search: "what do you remember about my preferences"
   - Delete: "delete that memory"
