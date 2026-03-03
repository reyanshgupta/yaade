Check the status of the Yaade memory server.

**Instructions:**
1. Call the `health_check` MCP tool (no parameters needed)

2. Display a clean status summary:

```
Yaade Memory Server
───────────────────
Status:          <healthy / unhealthy>
Memories stored: <total_memories>
Embedding model: <embedding_model>
Data directory:  <data_directory>
```

3. If status is **unhealthy**, show the error and suggest:
   - Restart Claude Code
   - Run `yaade serve` manually to check for errors
   - Set `YAADE_LOG_LEVEL=DEBUG` for verbose output

4. If status is **healthy** and `total_memories` is 0, gently remind the user they can start storing memories with `/remember <content>`.

**Prerequisite:** Yaade MCP server must be configured. If the tool is unavailable, tell the user to run `./setup/claude-code/setup-mcp-linux.sh` (or the macOS/Windows equivalent) and restart Claude Code.
