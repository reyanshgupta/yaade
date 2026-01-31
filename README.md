# Yaade - Memory Storage for AI Agents

**Yaade** (यादें) - Hindi for "memories" - is a local MCP-compatible server that provides centralized memory storage for multiple AI tools including Claude Desktop, Claude Code, and other MCP-compatible clients.

## Features

- **Semantic Memory Storage**: Store and retrieve memories using vector embeddings
- **Intelligent Search**: Search memories by meaning, not just keywords
- **MCP Compatible**: Full Model Context Protocol (MCP) v2025-06-18 support
- **Local-First**: No cloud dependencies, all data stays on your machine
- **TUI Interface**: Beautiful terminal UI for memory management
- **Easy Integration**: Works seamlessly with Claude Desktop and Claude Code

## Technology Stack

- **Protocol**: MCP (Model Context Protocol) with stdio/HTTP transports
- **Vector Database**: ChromaDB for semantic search and embedding storage
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) for local text encoding
- **Configuration**: Pydantic v2 with environment variable support
- **TUI**: Textual framework for terminal interface
- **Package Management**: UV for fast dependency management

## Installation

### Prerequisites

- Python 3.12+
- [UV package manager](https://docs.astral.sh/uv/getting-started/installation/)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/yaade.git
cd yaade

# Install dependencies with UV
uv sync

# Launch Yaade TUI
uv run yaade
```

## Quick Start

### Launch the TUI

```bash
uv run yaade
```

This opens the main interface where you can:
- Manage memories (add, edit, delete, search)
- Configure storage location
- Set up MCP integration with Claude Desktop/Code
- Customize themes

### TUI Navigation

```
┌─────────────────────────────────────────┐
│               Yaade                     │
│        Memory Storage for AI            │
├─────────────────────────────────────────┤
│  [1] Memory Management                  │
│  [2] Settings                           │
│  [Q] Quit                               │
└─────────────────────────────────────────┘
```

### Automated Setup Scripts

From the Settings menu in the TUI, you can run setup scripts for:

**Claude Desktop**: Configures `~/Library/Application Support/Claude/claude_desktop_config.json`

**Claude Code**: Configures `~/.claude.json`

Or run manually:

```bash
# Claude Desktop (macOS)
./setup/claude-desktop/setup-mcp-macos.sh

# Claude Code (macOS)
./setup/claude-code/setup-mcp-macos.sh
```

## CLI Commands

```bash
yaade              # Launch the TUI (default)
yaade serve        # Run MCP server (headless mode for Claude integration)
yaade --help       # Show help
yaade --version    # Show version
```

## Manual Claude Configuration

### Claude Desktop

Add this to your Claude Desktop config:

**Location**: 
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "yaade": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/yaade", "yaade", "serve"],
      "env": {
        "YAADE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Using Memory with Claude

Once configured, you can use natural language:

- **Store a memory**: "Remember that I prefer TypeScript over JavaScript"
- **Search memories**: "What do you remember about my programming preferences?"
- **Check status**: Ask Claude to check the memory server health

## Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_memory` | Store new memory with embedding | `content`, `memory_type`, `source`, `tags`, `importance`, `metadata` |
| `search_memories` | Semantic search across memories | `query`, `limit`, `filter_tags` |
| `get_memory` | Retrieve specific memory by ID | `memory_id` |
| `delete_memory` | Remove memory from storage | `memory_id` |
| `health_check` | Check server status and statistics | None |
| `analyze_memory_cleanup` | Find duplicate/similar memories | `similarity_threshold`, `consolidation_threshold` |
| `execute_memory_cleanup` | Execute cleanup with confirmation | `actions_to_execute`, `confirm_deletion` |

## Configuration

Configuration via environment variables. Create a `.env` file or set these:

```bash
# Storage Configuration
YAADE_DATA_DIR=.yaade

# Embedding Configuration  
YAADE_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
YAADE_EMBEDDING_BATCH_SIZE=32
YAADE_EMBEDDING_MAX_SEQ_LENGTH=512

# Server Configuration
YAADE_HOST=localhost
YAADE_PORT=8000
YAADE_LOG_LEVEL=INFO
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `YAADE_DATA_DIR` | `.yaade` | Base directory for data storage |
| `YAADE_EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `YAADE_EMBEDDING_BATCH_SIZE` | `32` | Batch size for embedding generation |
| `YAADE_LOG_LEVEL` | `INFO` | Logging level |

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude        │    │     Yaade        │    │  Storage        │
│   Desktop/Code  │◄──►│                  │◄──►│                 │
│                 │    │  - FastMCP       │    │ - ChromaDB      │
│  Other MCP      │    │  - Tools         │    │ - Embeddings    │
│  Clients        │    │  - Resources     │    │ - Metadata      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Components

- **FastMCP Server**: Handles MCP protocol communication
- **Vector Store**: ChromaDB for semantic search capabilities  
- **Embedding Service**: Local sentence-transformers for text encoding
- **TUI**: Textual-based terminal interface for management
- **Configuration**: Environment-based settings management

## Data Storage

- **Default Location**: `.yaade/`
- **Vector Database**: `.yaade/chroma/`
- **Logs**: Console output (configurable)

All data is stored locally on your machine. No data is sent to external services.

## Privacy & Security

- **Local-First**: All processing happens on your machine
- **No Telemetry**: ChromaDB telemetry is disabled
- **No External Calls**: Embeddings generated locally
- **Configurable**: Full control over data storage location

## Development

### Project Structure

```
yaade/
├── app/
│   ├── main.py              # FastMCP server entry point
│   ├── cli.py               # CLI entry point
│   ├── models/              # Pydantic data models
│   ├── storage/             # Storage backends (ChromaDB)
│   ├── search/              # Embedding services
│   ├── services/            # Business logic
│   └── tui/                 # Terminal UI
├── setup/                   # Setup scripts
│   ├── claude-desktop/
│   └── claude-code/
├── pyproject.toml
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

**TUI won't start**
- Check Python version (3.12+ required)
- Verify UV is installed and up to date
- Run `uv sync` to ensure dependencies are installed

**Claude not connecting**
- Verify config file path is correct
- Check that `cwd` points to your project directory
- Restart Claude Desktop/Code after config changes

**Import errors**
- Run `uv sync` to ensure dependencies are installed
- Check that you're in the correct directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com) for the MCP specification
- [ChromaDB](https://www.trychroma.com/) for the vector database
- [sentence-transformers](https://www.sbert.net/) for embeddings
- [Textual](https://textual.textualize.io/) for the TUI framework
- [UV](https://docs.astral.sh/uv/) for package management

---
