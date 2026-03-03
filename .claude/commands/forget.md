Delete a memory from Yaade:

$ARGUMENTS

**Instructions:**

**Case 1 — Argument is a UUID** (matches pattern `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`):
- Call `delete_memory` with that `memory_id` directly
- Confirm deletion with the ID and timestamp returned

**Case 2 — Argument is a description or phrase**:
1. Call `search_memories` with the phrase as the query (limit: 5)
2. Show the top results to the user with their content and IDs
3. Ask: "Which memory should I delete? (reply with the ID, or 'all' to delete all shown, or 'none' to cancel)"
4. Wait for the user to reply before deleting anything
5. Delete only after explicit confirmation

**Safety rule:** Never delete without showing the user what will be removed first. When in doubt, show results and ask.

**Prerequisite:** Yaade MCP server must be configured. If the tool is unavailable, tell the user to run `./setup/claude-code/setup-mcp-linux.sh` (or the macOS/Windows equivalent) and restart Claude Code.
