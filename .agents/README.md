# AI Agent Configurations

This directory contains configuration files for various AI coding assistants to help them understand and work with the Yaade codebase.

## Files

| File | AI Tool | Usage |
|------|---------|-------|
| `AGENTS.md` | All | **Central template** - comprehensive project documentation |
| `CLAUDE.md` | Claude Code | Symlink to project root |
| `.cursorrules` | Cursor | Symlink to project root |
| `OPENCODE.md` | OpenCode | Symlink to project root |
| `WINDSURF.md` | Windsurf/Codeium | Symlink to project root |
| `CODY.md` | Sourcegraph Cody | Reference file |
| `ANTIGRAVITY.md` | Antigravity | Symlink to project root |
| `continue.json` | Continue | Copy to `.continue/config.json` |
| `.aider.conf.yml` | Aider | Symlink to project root |

## Quick Setup

### Option 1: Run the setup script

```bash
./.agents/setup.sh
```

### Option 2: Manual symlinks

```bash
# From project root
ln -sf .agents/CLAUDE.md CLAUDE.md
ln -sf .agents/.cursorrules .cursorrules
ln -sf .agents/.aider.conf.yml .aider.conf.yml
```

## Adding a New AI Tool

1. Create a new file in `.agents/` (e.g., `NEWTOOL.md`)
2. Use `AGENTS.md` as the comprehensive reference
3. Include tool-specific format/syntax as needed
4. Add to this README
5. Update `setup.sh` if symlink needed

## File Format Guidelines

- **Markdown files** (`.md`): Most AI tools accept markdown instructions
- **JSON files** (`.json`): For tools with structured config (Continue)
- **YAML files** (`.yml`): For tools using YAML config (Aider)
- **Rules files** (`.cursorrules`, etc.): Tool-specific formats

## Content Structure

Each config file should include:

1. **Project summary** - What Yaade is
2. **Tech stack** - Key technologies
3. **Project structure** - Important directories/files
4. **Commands** - How to run, test, build
5. **Code conventions** - Style guidelines
6. **Critical rules** - What NOT to do
7. **Reference** - Link to full `AGENTS.md`

## Keeping Updated

When making significant changes to the project:

1. Update `AGENTS.md` first (source of truth)
2. Propagate key changes to tool-specific files
3. Test with at least one AI tool to verify accuracy
