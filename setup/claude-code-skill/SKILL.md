---
name: yaade
version: 1.0.0
description: |
  Interact with Yaade semantic memory storage. Use when the user wants to:
  - Remember or store information ("remember this", "save this for later")
  - Recall or search memories ("what do you remember about", "search memories")
  - Manage memories (view, delete, clean up duplicates)
  - Check memory server status
  Provides persistent cross-session memory for AI agents.
allowed-tools:
  - ToolSearch
  - AskUserQuestion
---

# Yaade: Semantic Memory for AI Agents

You are interacting with Yaade (याद), a semantic memory storage system. Memories persist across conversations and are searchable by meaning, not just keywords.

## Setup (Required First)

Before ANY memory operation, load the Yaade MCP tools:

Use ToolSearch with query: "+yaade"

This loads all Yaade tools. Only proceed after they appear in results.

## Operations

### Store a Memory

When the user wants to remember something:

1. Extract the core fact or information
2. Call `mcp__yaade__add_memory` with:
   - `content`: The information to store (make it self-contained and useful)
   - `memory_type`: "text" (default), "code", "conversation", or "document"
   - `source`: "claude" (always use this when you're storing)
   - `tags`: Derive from context, e.g., ["preferences", "typescript"], ["project", "api"]
   - `importance`: 1.0 default, higher (up to 10) for explicitly important items
3. Confirm storage with the memory_id

**Good memory content:**
- "User prefers TypeScript over JavaScript for new projects due to type safety"
- "Project uses PostgreSQL with Prisma ORM, deployed on Railway"

**Bad memory content:**
- "prefers typescript" (too vague)
- "database stuff" (not useful later)

### Search Memories

When the user wants to recall information:

1. Formulate a semantic query from their request
2. Call `mcp__yaade__search_memories` with:
   - `query`: Natural language search (meaning-based, not keyword-based)
   - `limit`: 10 default, adjust based on need
   - `filter_tags`: Optional, to narrow by category
3. Present results with content, similarity score, and tags
4. If no results, suggest alternative terms

**Tips:**
- Use natural language: "user's database preferences" not "database"
- Higher similarity scores (closer to 1.0) = more relevant

### View a Specific Memory

Use `mcp__yaade__get_memory` with the `memory_id` to see full details.

### Delete a Memory

1. **Always confirm with the user first**
2. Call `mcp__yaade__delete_memory` with the `memory_id`
3. Report the result

### Clean Up Duplicates

1. First run `mcp__yaade__analyze_memory_cleanup` to preview what would be cleaned
2. Present the analysis to the user
3. Only call `mcp__yaade__execute_memory_cleanup` with `confirm_deletion=True` after explicit user approval

**Never auto-execute cleanup** - always require user confirmation.

### Health Check

Use `mcp__yaade__health_check` when:
- User asks about memory status
- Operations are failing
- User wants to know memory count

## When to Proactively Store

Suggest storing when the user shares:
- Personal preferences (coding style, tools, frameworks)
- Project patterns or conventions
- Important decisions and rationale
- Frequently referenced information

Ask: "Would you like me to remember this?"

**Do NOT store:**
- Temporary information
- Sensitive data (passwords, API keys, personal info)
- Information the user hasn't validated

## Error Handling

If operations fail, run `health_check` first. If unhealthy, tell the user:
"The Yaade memory server isn't responding. Ensure it's running with `yaade serve`."
