# Yaade - OpenCode Instructions

> Configuration for OpenCode AI assistant. Symlink or copy to project root.

## Project

**Yaade** (यादें) - Local MCP memory storage server for AI agents with semantic search.

**Stack**: Python 3.12+, ChromaDB, sentence-transformers, Textual TUI, FastMCP

## Structure

```
app/
├── cli.py              # CLI entry (yaade, yaade serve)
├── main.py             # MCP server + tools
├── models/             # Pydantic v2 models
├── storage/            # ChromaDB vector store
├── search/             # Embedding service
├── services/           # Business logic
└── tui/                # Textual TUI
    ├── screens/        # UI screens
    ├── modals/         # Modal dialogs
    └── themes.py       # Color themes
```

## Commands

```bash
uv sync                 # Install
uv run yaade            # TUI
uv run yaade serve      # MCP server
uv run pytest           # Tests
```

## Style

- Type hints required
- Pydantic v2 models
- Async MCP tools
- snake_case files, PascalCase classes

## Rules

1. **Local-first** - No external APIs
2. **No telemetry** - ChromaDB telemetry disabled
3. **Main thread embeddings** - TUI compatibility
4. **ConfigManager for .env** - Don't modify directly

## MCP Tools

add_memory, search_memories, get_memory, delete_memory, health_check, analyze_memory_cleanup, execute_memory_cleanup

## Env Vars (YAADE_ prefix)

DATA_DIR, EMBEDDING_MODEL_NAME, LOG_LEVEL, THEME

---

Full docs: `.agents/AGENTS.md`
