# Yaade - Antigravity Instructions

> Configuration for Antigravity AI assistant.

## Project

**Yaade** (यादें) - Local MCP memory storage server for AI agents with semantic search.

**Stack**: Python 3.12+, UV, ChromaDB, sentence-transformers, Textual, FastMCP, Pydantic v2

## Structure

- `app/cli.py` - CLI entry point
- `app/main.py` - MCP server + tools
- `app/models/` - Pydantic models (config, memory, embedding_models)
- `app/storage/vector_store.py` - ChromaDB operations
- `app/search/embeddings.py` - Embedding service
- `app/services/memory_cleanup.py` - Duplicate detection
- `app/tui/` - Textual TUI (app, screens, modals, themes)
- `tests/` - pytest test suite

## Commands

```bash
uv sync                 # Install
uv run yaade            # TUI
uv run yaade serve      # MCP server
uv run pytest           # Tests
```

## Rules

1. **Local-first** - No external API calls
2. **No telemetry** - ChromaDB telemetry disabled
3. **Main thread embeddings** - Required for TUI compatibility
4. **ConfigManager** - Use for .env modifications
5. **Type hints** - Required on all functions

## MCP Tools

add_memory, search_memories, get_memory, delete_memory, health_check, analyze_memory_cleanup, execute_memory_cleanup

## Env Vars (YAADE_ prefix)

DATA_DIR, EMBEDDING_MODEL_NAME, LOG_LEVEL, THEME

---

Full documentation: `.agents/AGENTS.md`
