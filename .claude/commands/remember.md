Store the following content as a persistent memory in Yaade:

$ARGUMENTS

**Instructions:**
1. Call the `add_memory` MCP tool with:
   - `content`: the text above (verbatim, do not summarize)
   - `memory_type`: infer from content — `code` for code snippets, `conversation` for decisions/discussions, `document` for notes/docs, `text` for everything else
   - `source`: `"claude"`
   - `tags`: generate 2–4 concise lowercase tags based on the subject matter
   - `importance`: rate 1.0–10.0 based on how useful this memory would be in future sessions (prefer 5.0 for general info, 8.0+ for architecture decisions or hard-won knowledge)

2. After storing, confirm with a one-line summary:
   - What was stored
   - The memory ID (so the user can reference or delete it later)
   - The tags applied

**Prerequisite:** Yaade MCP server must be configured. If the tool is unavailable, tell the user to run `./setup/claude-code/setup-mcp-linux.sh` (or the macOS/Windows equivalent) and restart Claude Code.
