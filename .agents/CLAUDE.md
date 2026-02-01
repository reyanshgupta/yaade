# Yaade - Claude Code Instructions

> This file configures Claude Code for the Yaade project. Symlink or copy to project root as `CLAUDE.md`.

## Project Summary

Yaade (यादें) is a local MCP-compatible memory storage server for AI agents with semantic search. Python 3.12+, ChromaDB, sentence-transformers, Textual TUI.

## Quick Reference

### Entry Points
- `app/cli.py` - CLI (`yaade`, `yaade serve`)
- `app/main.py` - MCP server with FastMCP
- `app/tui/app.py` - Textual TUI application

### Key Directories
- `app/models/` - Pydantic v2 models (config, memory, embedding_models)
- `app/storage/` - ChromaDB vector store
- `app/search/` - Embedding service
- `app/services/` - Business logic (memory_cleanup)
- `app/tui/` - Terminal UI (screens, modals, widgets, themes)
- `setup/` - MCP setup scripts for Claude Desktop/Code/OpenCode
- `tests/` - pytest test suite

### Commands
```bash
uv sync                          # Install deps
uv run yaade                     # Launch TUI
uv run yaade serve               # Run MCP server
uv run pytest                    # Run tests
uv run pytest --cov=app          # Tests with coverage
```

## Code Style

- Type hints on all functions
- Pydantic v2 for models
- Google-style docstrings
- Async for MCP tools
- snake_case files/functions, PascalCase classes

## Architecture

```
AI Clients ◄──► FastMCP Server ◄──► ChromaDB + Embeddings
                    │
              Memory Service
                    │
               Textual TUI
```

## Important Constraints

1. **Local-first**: No external API calls, all processing local
2. **No telemetry**: ChromaDB telemetry explicitly disabled
3. **TUI threading**: Embedding generation on main thread only (PyTorch/Textual conflict)
4. **Config changes**: Use `ConfigManager` for `.env` modifications

## MCP Tools

`add_memory`, `search_memories`, `get_memory`, `delete_memory`, `health_check`, `analyze_memory_cleanup`, `execute_memory_cleanup`

## Testing

Mirror `app/` structure in `tests/unit/`. Use `pytest-asyncio` for async tests.

## Environment Variables

All prefixed with `YAADE_`: `DATA_DIR`, `EMBEDDING_MODEL_NAME`, `LOG_LEVEL`, `THEME`

---

For full documentation, see `.agents/AGENTS.md`
