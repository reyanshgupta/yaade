# Yaade - AI Agent Instructions

This is the central configuration for AI coding agents working on the Yaade project. Copy or symlink this file for your preferred AI tool.

## Project Overview

**Yaade** (यादें - Hindi for "memories") is a local MCP-compatible memory storage server for AI agents. It provides semantic search capabilities using vector embeddings, with a TUI for management and CLI for server operations.

### Key Technologies

- **Language**: Python 3.12+
- **Package Manager**: UV (preferred) or pip
- **Vector Database**: ChromaDB
- **Embeddings**: sentence-transformers
- **TUI Framework**: Textual
- **MCP Protocol**: FastMCP with stdio transport
- **Configuration**: Pydantic v2 Settings
- **Testing**: pytest with asyncio support

## Project Structure

```
yaade/
├── app/                          # Main application code
│   ├── main.py                   # FastMCP server entry point
│   ├── cli.py                    # CLI entry point (typer)
│   ├── models/                   # Pydantic data models
│   │   ├── config.py             # Server configuration (env vars)
│   │   ├── memory.py             # Memory and MemoryCollection models
│   │   └── embedding_models.py   # Supported embedding model definitions
│   ├── storage/                  # Database layer
│   │   └── vector_store.py       # ChromaDB vector storage
│   ├── search/                   # Embedding services
│   │   ├── embeddings.py         # Sentence-transformer service
│   │   └── model_downloader.py   # Model management CLI
│   ├── services/                 # Business logic
│   │   └── memory_cleanup.py     # Duplicate detection & consolidation
│   └── tui/                      # Terminal UI (Textual)
│       ├── app.py                # Main TUI application
│       ├── memory_manager.py     # Memory operations manager
│       ├── themes.py             # Custom color themes
│       ├── screens/              # UI screens
│       │   ├── main_menu.py
│       │   ├── memory_management.py
│       │   └── modals/           # Modal dialogs
│       ├── settings/             # Settings screens
│       │   ├── settings_screen.py
│       │   └── setup_screen.py
│       ├── widgets/              # Custom Textual widgets
│       └── utils/                # TUI utilities
├── setup/                        # Client setup scripts
│   ├── claude-desktop/           # Claude Desktop MCP setup
│   ├── claude-code/              # Claude Code MCP setup
│   └── opencode/                 # OpenCode MCP setup
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests (mirrors app/ structure)
│   └── integration/              # Integration tests
├── .agents/                      # AI agent configurations (this directory)
├── install.sh                    # Source installation script
├── uninstall.sh                  # Uninstallation script
└── pyproject.toml                # Project configuration
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Clients    │    │     Yaade        │    │  Storage        │
│                 │    │                  │    │                 │
│  Claude Desktop │◄──►│  FastMCP Server  │◄──►│  ChromaDB       │
│  Claude Code    │    │  MCP Tools       │    │  Embeddings     │
│  OpenCode       │    │  Memory Service  │    │  Metadata       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **MCP Server** (`app/main.py`) receives tool calls via stdio
2. **Memory operations** use `EmbeddingService` for vector encoding
3. **VectorStore** persists to ChromaDB with embeddings and metadata
4. **TUI** provides direct database access for management

## Code Conventions

### Python Style

- Use type hints for all function signatures
- Pydantic v2 models for data validation
- Async functions where appropriate (MCP tools are async)
- Docstrings for public functions (Google style)

### Imports

```python
# Standard library
from datetime import datetime
from typing import Optional, List, Dict, Any

# Third-party
from pydantic import BaseModel, Field
from textual.app import App
from mcp.server.fastmcp import FastMCP

# Local
from app.models.config import settings
from app.storage.vector_store import VectorStore
```

### Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_`

### Error Handling

- Use specific exception types
- Log errors with context
- Return meaningful error messages to users

## Key Files Reference

### Entry Points

- `app/cli.py` - CLI commands (`yaade`, `yaade serve`, `yaade download-model`)
- `app/main.py` - MCP server with tool definitions
- `app/tui/app.py` - TUI application entry

### Core Models

- `app/models/memory.py` - `Memory`, `MemoryType`, `MemorySource`, `MemoryCollection`
- `app/models/config.py` - `Settings` (Pydantic Settings with YAADE_ prefix)
- `app/models/embedding_models.py` - `SUPPORTED_MODELS` dict with model specs

### Services

- `app/storage/vector_store.py` - `VectorStore` class for ChromaDB operations
- `app/search/embeddings.py` - `EmbeddingService` for sentence-transformers
- `app/services/memory_cleanup.py` - `MemoryCleanupService` for deduplication

### TUI Components

- `app/tui/memory_manager.py` - `MemoryManager` with sync/async wrappers
- `app/tui/themes.py` - Theme definitions (cyberpunk, cyberpunk_soft, neon_nights)
- `app/tui/screens/` - Screen classes (MainMenuScreen, MemoryManagementScreen)
- `app/tui/screens/modals/` - Modal dialogs (AddMemoryModal, EditMemoryModal, etc.)

## MCP Tools

The server exposes these tools via MCP:

| Tool | Purpose |
|------|---------|
| `add_memory` | Store memory with embedding |
| `search_memories` | Semantic similarity search |
| `get_memory` | Retrieve by ID |
| `delete_memory` | Remove memory |
| `health_check` | Server status |
| `analyze_memory_cleanup` | Find duplicates (non-destructive) |
| `execute_memory_cleanup` | Execute cleanup with confirmation |

## Testing

### Running Tests

```bash
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest --cov=app          # With coverage
uv run pytest -v -s              # Verbose with output
```

### Test Structure

- Mirror the `app/` directory structure in `tests/unit/`
- Use `pytest-asyncio` for async tests
- Use `pytest-mock` for mocking
- Fixtures in `conftest.py`

### Writing Tests

```python
import pytest
from app.models.memory import Memory, MemoryType

def test_memory_creation():
    memory = Memory(
        content="Test content",
        type=MemoryType.TEXT,
    )
    assert memory.content == "Test content"
    assert memory.id is not None

@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

## Common Patterns

### Adding a New MCP Tool

1. Define the tool in `app/main.py`:
```python
@mcp.tool()
async def new_tool(param: str) -> dict:
    """Tool description."""
    # Implementation
    return {"status": "success"}
```

### Adding a New TUI Screen

1. Create screen in `app/tui/screens/new_screen.py`
2. Inherit from `Screen`
3. Define `compose()` method for widgets
4. Add navigation in parent screen

### Adding a New Modal

1. Create in `app/tui/screens/modals/new_modal.py`
2. Inherit from `ModalScreen`
3. Handle dismiss with result

### Modifying Configuration

1. Add field to `app/models/config.py` Settings class
2. Use `YAADE_` prefix for env var
3. Update README Configuration section

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `YAADE_DATA_DIR` | `.yaade` | Data storage location |
| `YAADE_EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Embedding model |
| `YAADE_EMBEDDING_BATCH_SIZE` | `32` | Batch size |
| `YAADE_LOG_LEVEL` | `INFO` | Logging level |
| `YAADE_THEME` | `cyberpunk` | TUI theme |

## DO NOT

- **Do not** add external API calls - this is a local-first application
- **Do not** enable ChromaDB telemetry - it's explicitly disabled
- **Do not** use threading in TUI embedding operations - causes PyTorch conflicts
- **Do not** modify `.env` without using `ConfigManager`
- **Do not** skip type hints on public functions
- **Do not** add dependencies without updating `pyproject.toml`

## Development Commands

```bash
# Install dependencies
uv sync

# Run TUI
uv run yaade

# Run MCP server
uv run yaade serve

# Run tests
uv run pytest

# Build package
uv run python -m build

# Format check (if configured)
uv run ruff check app/
```

## Contributing Workflow

1. Create feature branch from `main`
2. Make changes following conventions above
3. Add/update tests
4. Run test suite
5. Update README if needed
6. Create pull request

## Useful Context

- MCP spec: https://spec.modelcontextprotocol.io/
- Textual docs: https://textual.textualize.io/
- ChromaDB docs: https://docs.trychroma.com/
- sentence-transformers: https://www.sbert.net/
