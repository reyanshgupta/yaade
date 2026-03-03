Analyze and optionally clean up duplicate or redundant memories in Yaade.

**Instructions:**

**Step 1 — Analyze (always run first, non-destructive):**
Call `analyze_memory_cleanup` with default thresholds:
- `similarity_threshold`: 0.85
- `consolidation_threshold`: 0.70

**Step 2 — Present the analysis clearly:**

Show a summary table:

```
Cleanup Analysis
────────────────────────────────
Exact duplicates:      <count> groups  (<n> memories to remove)
Near-duplicates:       <count> groups  (<n> memories to remove)
Consolidation groups:  <count> groups  (<n> memories to merge)

Estimated reduction: <current> → <after> memories (<% saved>)
```

Then list each group briefly (first 50 chars of content + similarity score).

**Step 3 — Ask the user what to do:**

"Which cleanup actions should I run? (Select all that apply, or 'none' to cancel)
  1. exact_duplicates — remove identical content
  2. near_duplicates  — remove very similar content (≥85% similar)
  3. consolidation    — merge related memories into single entries
  4. all              — run all three
  5. none             — cancel"

**Step 4 — Execute only after confirmation:**
- Only if the user selected actions (not 'none')
- Call `execute_memory_cleanup` with:
  - `actions_to_execute`: the selected action names
  - `confirm_deletion`: true

**Step 5 — Show results:**
Report how many memories were deleted/merged and the final memory count.

**Safety rule:** Never call `execute_memory_cleanup` without first showing the analysis and getting explicit user choice.

**Prerequisite:** Yaade MCP server must be configured. If the tool is unavailable, tell the user to run `./setup/claude-code/setup-mcp-linux.sh` (or the macOS/Windows equivalent) and restart Claude Code.
