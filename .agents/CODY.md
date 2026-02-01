# Yaade - Cody Instructions

> Sourcegraph Cody configuration for the Yaade project.

## Project

Yaade is a local MCP-compatible memory storage server for AI agents with semantic search capabilities.

## Tech Stack

- Python 3.12+
- ChromaDB (vector database)
- sentence-transformers (local embeddings)
- Textual (TUI framework)
- FastMCP (MCP protocol)
- Pydantic v2 (models)
- pytest (testing)

## Key Files

| File | Purpose |
|------|---------|
| `app/cli.py` | CLI commands |
| `app/main.py` | MCP server + tools |
| `app/models/config.py` | Settings (env vars) |
| `app/models/memory.py` | Memory models |
| `app/storage/vector_store.py` | ChromaDB ops |
| `app/search/embeddings.py` | Embedding service |
| `app/tui/app.py` | TUI entry |

## Development

```bash
uv sync              # Install
uv run yaade         # TUI
uv run yaade serve   # MCP server
uv run pytest        # Tests
```

## Conventions

- Type hints on all functions
- Pydantic v2 for validation
- Async MCP tools
- Tests mirror app/ structure

## Critical

- Local-first: no external APIs
- No telemetry
- Main thread for embeddings in TUI

Full documentation: `.agents/AGENTS.md`
