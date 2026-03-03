Search Yaade for memories relevant to:

$ARGUMENTS

**Instructions:**
1. Call `search_memories` with:
   - `query`: the search text above
   - `limit`: 8

2. Format results as a ranked list. For each result show:
   - **Relevance**: `similarity_score` as a percentage (e.g., 94%)
   - **Content**: the memory content
   - **Tags**: from metadata
   - **ID**: the memory_id (small, monospaced) so the user can reference it

3. If no results are found (empty list or all scores below 40%), say so clearly and suggest a broader search term.

4. If results look highly relevant (score > 85%), proactively offer to use the content in the current task.

**Prerequisite:** Yaade MCP server must be configured. If the tool is unavailable, tell the user to run `./setup/claude-code/setup-mcp-linux.sh` (or the macOS/Windows equivalent) and restart Claude Code.
