# Yaade - Windsurf/Codeium Instructions

> Configuration for Windsurf (Codeium) AI assistant.

## Project Overview

**Yaade** (यादें) - Local MCP-compatible memory storage server for AI agents with semantic search.

## Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12+ | Language |
| UV | Package manager |
| ChromaDB | Vector database |
| sentence-transformers | Local embeddings |
| Textual | TUI framework |
| FastMCP | MCP protocol |
| Pydantic v2 | Data models |
| pytest | Testing |

## Project Layout

```
app/
├── cli.py              # yaade, yaade serve, yaade download-model
├── main.py             # FastMCP server with MCP tools
├── models/
│   ├── config.py       # Settings (YAADE_ env vars)
│   ├── memory.py       # Memory, MemoryType, MemorySource
│   └── embedding_models.py
├── storage/
│   └── vector_store.py # ChromaDB operations
├── search/
│   ├── embeddings.py   # EmbeddingService
│   └── model_downloader.py
├── services/
│   └── memory_cleanup.py
└── tui/
    ├── app.py          # YaadeApp (Textual)
    ├── memory_manager.py
    ├── themes.py
    ├── screens/
    └── settings/
```

## Commands

```bash
uv sync                 # Install dependencies
uv run yaade            # Launch TUI
uv run yaade serve      # Start MCP server
uv run pytest           # Run tests
uv run pytest --cov=app # With coverage
```

## Code Style

- **Type hints**: Required on all public functions
- **Models**: Pydantic v2 with validation
- **Async**: MCP tools are async
- **Docstrings**: Google style
- **Naming**: snake_case files, PascalCase classes

## Critical Constraints

| Rule | Reason |
|------|--------|
| No external APIs | Local-first architecture |
| No telemetry | Privacy - ChromaDB telemetry disabled |
| Main thread embeddings | PyTorch/Textual threading conflict |
| Use ConfigManager | Proper .env file handling |

## MCP Tools

- `add_memory` - Store with embedding
- `search_memories` - Semantic search
- `get_memory` - Retrieve by ID
- `delete_memory` - Remove
- `health_check` - Status
- `analyze_memory_cleanup` - Find duplicates
- `execute_memory_cleanup` - Clean with confirmation

## Environment Variables

Prefix: `YAADE_`

- `DATA_DIR` - Storage location (default: `.yaade`)
- `EMBEDDING_MODEL_NAME` - Model (default: `all-MiniLM-L6-v2`)
- `LOG_LEVEL` - Logging (default: `INFO`)
- `THEME` - TUI theme (default: `cyberpunk`)

---

Full documentation: `.agents/AGENTS.md`
