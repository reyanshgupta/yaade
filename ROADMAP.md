# Yaade — v0.1 Release Roadmap

> Last updated: March 2026
> Target: first stable public release on PyPI

This document describes the work required to ship Yaade **v0.1.0** — a stable, public, production-worthy release. It is derived from the full UX & bug audit (`BUG_REPORT.md`) and from a review of the existing feature set.

---

## Guiding Principles for v0.1

1. **No data loss.** Every write-path must be safe. No silent failures, no "TODO" placeholders in destructive code paths.
2. **Clear feedback.** Users must always know what just happened — success, failure, or in-progress.
3. **Honest documentation.** The README must only describe features that actually work.
4. **Single-user, local-first.** v0.1 is explicitly a local tool; no multi-user or cloud features.
5. **Minimal but complete.** Ship fewer features that work perfectly rather than many that are half-built.

---

## Milestones

```
M1 (Blocker fixes)  ──►  M2 (Core UX)  ──►  M3 (Polish & Docs)  ──►  v0.1.0 Release
```

---

## Milestone 1 — Blocker Bug Fixes

**Goal:** Eliminate every issue that causes data loss, silent failures, or crashes.
All items in this milestone are **release blockers**.

### M1.1 — Fix or disable the Consolidation action (BUG-001)

| | |
|---|---|
| **File** | `app/services/memory_cleanup.py:487–512` |
| **Bug ID** | BUG-001 |

**Option A (Preferred for v0.1):** Remove `"consolidation"` from the list of supported `actions_to_execute` values in `execute_memory_cleanup`. Return a clear error message if it is requested: `"Consolidation is not yet implemented. Use near_duplicates to merge similar memories."` Update the README and MCP tool docstring accordingly.

**Option B (Full implementation, target v0.2):** Inject `EmbeddingService` into `MemoryCleanupService`, synthesise a consolidated text, store it as a new memory, then delete the originals. Return the new memory ID.

---

### M1.2 — Fix hardcoded embedding dimension in cleanup analysis (BUG-002)

| | |
|---|---|
| **File** | `app/services/memory_cleanup.py:236` |
| **Bug ID** | BUG-002 |

Replace `[0.0] * 384` with a dimension derived from the configured model:

```python
from app.models.embedding_models import EMBEDDING_MODELS
dim = EMBEDDING_MODELS[config.embedding_model_name].dimensions
dummy_embedding = [0.0] * dim
```

Also pass `include=["embeddings", "documents", "metadatas"]` to the ChromaDB query so near-duplicate similarity is computed against real stored vectors (BUG-023).

---

### M1.3 — Preserve memory ID and `created_at` on edit (BUG-005)

| | |
|---|---|
| **File** | `app/tui/memory_manager.py:323–350` |
| **Bug ID** | BUG-005 |

Use ChromaDB's `Collection.update()` API to update the document and metadata in-place rather than deleting and re-adding. Preserve the original UUID and `created_at` field. The `VectorStore` layer should expose an `update_memory(id, ...)` method that does this atomically.

---

### M1.4 — Replace double-keypress delete with a modal confirmation (BUG-006)

| | |
|---|---|
| **File** | `app/tui/screens/memory_management.py:395–456` |
| **Bug ID** | BUG-006 |

Replace the timed double-keypress pattern with a `ConfirmDeleteModal` dialog that:
- Shows the full memory content (not truncated)
- Has **Delete** (destructive, red) and **Cancel** buttons
- Requires an explicit confirmation click or Enter keypress

Remove `_pending_delete_row`, `_pending_delete_time`, `_delete_confirm_timeout`, and `_show_delete_confirmation_in_row`.

---

### M1.5 — Handle ChromaDB corruption gracefully (BUG-009)

| | |
|---|---|
| **File** | `app/storage/vector_store.py` (constructor) |
| **Bug ID** | BUG-009 |

Wrap `chromadb.PersistentClient()` in a try/except. On failure:
1. Show a clear error screen in the TUI: "Database could not be opened. It may be corrupted."
2. Offer two buttons: **Open data directory** (opens the folder in a file manager) and **Reinitialise** (moves the corrupt directory to `~/.yaade/chroma.bak.<timestamp>` and creates a fresh one).

---

### M1.6 — Validate and sanitise the storage path before saving (BUG-008, SEC-001)

| | |
|---|---|
| **Files** | `app/tui/settings/onboarding_screen.py:94–99`, `app/tui/screens/modals/storage_config.py:65–76` |
| **Bug IDs** | BUG-008, SEC-001 |

After `os.path.expanduser()`, call `Path(path).resolve()`. Attempt to create the directory and write a test file. If that fails, show a specific error (permission denied, disk full, invalid path) and do **not** persist the value.

---

### M1.7 — Make embedding model ID validation strict (SEC-003)

| | |
|---|---|
| **File** | `app/search/embeddings.py`, `app/tui/screens/modals/embedding_model_select.py` |
| **Bug ID** | SEC-003 |

Before loading or downloading any model, verify the model ID is in the `EMBEDDING_MODELS` allowlist defined in `app/models/embedding_models.py`. Raise a clear `ValueError` with a helpful message if the ID is not recognised.

---

## Milestone 2 — Core UX Improvements

**Goal:** Make every common user flow — add, view, edit, delete, search — complete and comprehensible.

### M2.1 — Implement in-TUI semantic search (BUG-003)

| | |
|---|---|
| **File** | `app/tui/memory_manager.py:399–406`, `app/tui/screens/memory_management.py` |
| **Bug ID** | BUG-003 |

Wire `search_memories` in `TUIMemoryManager` to the actual `VectorStore.search_similar()` method. Add a search bar to the Memory Management screen (shortcut `/` or `s`). Show results in a separate panel or replace the full list with filtered results. Add a **Clear search** shortcut.

---

### M2.2 — Add a read-only memory detail view (BUG-014)

| | |
|---|---|
| **File** | `app/tui/screens/memory_management.py` |
| **Bug ID** | BUG-014 |

Add a `v` (or Enter) keybinding on the memory list table that opens a `MemoryDetailModal` showing:
- Full content (scrollable)
- Memory type, source, tags, importance
- Created and updated timestamps
- Memory ID (copyable)

---

### M2.3 — Show "X of N memories shown" and add Load More (BUG-013)

| | |
|---|---|
| **File** | `app/tui/screens/memory_management.py:200` |
| **Bug ID** | BUG-013 |

Remove the hard 50-memory cap. Add a `page` concept (or increase limit to 500 and add a virtual-scroll DataTable). Show `"Showing X of N memories"` in the stats bar. Add a `Load More` button or `PgDn` keybinding.

---

### M2.4 — Friendly embedding generation error messages (BUG-010)

| | |
|---|---|
| **File** | `app/tui/memory_manager.py:110–116` |
| **Bug ID** | BUG-010 |

Map common exception types to human-readable messages:

| Exception | User message |
|---|---|
| `OSError: No space left on device` | "Disk full — free up space and try again." |
| `RuntimeError: Model not loaded` | "Embedding model not downloaded. Run: yaade download-model download <name>" |
| ChromaDB dimension mismatch | "Embedding model mismatch — re-index your database in Settings." |

Show errors as **persistent** notifications (not auto-dismiss) with a **Dismiss** button.

---

### M2.5 — Fix theme-on-highlight race condition (BUG-011)

| | |
|---|---|
| **File** | `app/tui/screens/memory_management.py:468–479` |
| **Bug ID** | BUG-011 |

Store the current theme when the Theme modal opens. Preview theme changes on highlight (keep this UX — it is nice). On **Cancel**, restore the stored theme. On **Apply**, persist the new theme to `.env`.

---

### M2.6 — Pre-fill Importance default and add character counter (UX-007, UX-002)

| | |
|---|---|
| **Files** | `app/tui/screens/modals/add_memory.py`, `edit_memory.py` |
| **Bug IDs** | UX-007, UX-002 |

- Pre-fill importance field with `"1.0"`.
- Show a live character counter below the content TextArea (e.g. `"1,247 characters"`).
- Add distinct error messages for non-numeric vs. out-of-range importance.

---

### M2.7 — Warn before storage path change (BUG-017)

| | |
|---|---|
| **File** | `app/tui/settings/settings_screen.py:280–293` |
| **Bug ID** | BUG-017 |

Show a confirmation dialog:

> "Changing the storage location will not migrate your existing memories. They will remain in the old location but will not be visible in Yaade until you change the path back.
> Continue?"

Offer **Continue** and **Cancel**.

---

### M2.8 — Emit ConfigManager write failures as visible notifications (BUG-012)

| | |
|---|---|
| **File** | `app/tui/utils/config_manager.py:50–93` |
| **Bug ID** | BUG-012 |

Log the exception type and message before returning `False`. All callers must check the return value and, on `False`, show a **persistent** error notification:

> "Failed to save setting — check file permissions for .env at <path>."

---

## Milestone 3 — Polish, Testing & Documentation

**Goal:** Ship a product users can trust and contributors can grow.

### M3.1 — Update README to match actual feature state

| | |
|---|---|
| **File** | `README.md` |

- Remove or mark as "coming soon" any feature that is not implemented:
  - TUI search (if M2.1 is not complete)
  - Memory consolidation (if M1.1 goes with Option A)
- Add a **Current Limitations** section.
- Add keyboard shortcuts table covering all BINDINGS defined in each screen.
- Clarify "restart the server" means `yaade serve`, not the TUI.

---

### M3.2 — Persist setup log to `~/.yaade/setup.log` (BUG-018)

| | |
|---|---|
| **File** | `app/tui/settings/setup_screen.py:277–294` |
| **Bug ID** | BUG-018 |

Write the full stdout/stderr of each setup script run to `~/.yaade/setup.log` with a timestamp. Show a "View log" link in the Setup screen after a run completes.

---

### M3.3 — Add `r` refresh shortcut to footer (UX-004)

| | |
|---|---|
| **File** | `app/tui/screens/memory_management.py` |

Add `Binding("r", "refresh", "Refresh")` to BINDINGS. The footer will then show it automatically.

---

### M3.4 — Write integration tests for all MCP tools end-to-end

| | |
|---|---|
| **File** | `tests/integration/test_mcp_tools.py` |

The existing integration test file exists but was not confirmed as exercising the real ChromaDB path. Add tests that:
- Spin up an in-memory ChromaDB
- Call all 7 MCP tools
- Verify `search_memories` returns semantically relevant results
- Verify `execute_memory_cleanup` with `exact_duplicates` correctly deduplicates
- Verify `consolidation` returns a descriptive not-implemented error (per M1.1 Option A)

---

### M3.5 — Add CI test matrix and coverage gate

| | |
|---|---|
| **File** | `.github/workflows/` |

- Add a `ci.yml` workflow that runs `uv run pytest --cov=app --cov-fail-under=70` on every pull request.
- Test on Python 3.12 and 3.13.
- Block merges if coverage drops below 70%.

---

### M3.6 — First-run splash screen with download progress (UX-006)

| | |
|---|---|
| **File** | `app/tui/app.py` |

Detect first run (no ChromaDB directory exists). Show a welcome screen with:
- Brief description of Yaade
- Progress bar for the default model download
- "Skip" option (launch without downloading, show a warning that memories cannot be added until a model is available)

---

### M3.7 — Bump version and tag v0.1.0

| | |
|---|---|
| **File** | `pyproject.toml` |

- Set `version = "0.1.0"`.
- Ensure `release.yml` GitHub Actions workflow triggers on `v0.1.0` tag and publishes to PyPI.
- Verify the PyPI package includes all required files.
- Write a `CHANGELOG.md` entry for v0.1.0.

---

## Summary Table

| Milestone | Items | Blocking? | Estimated Effort |
|---|---|---|---|
| M1 — Blocker Bug Fixes | 7 | Yes | Medium |
| M2 — Core UX | 8 | Recommended | Medium |
| M3 — Polish & Docs | 7 | No | Small |

All of M1 must be complete before any public announcement. M2 items that are not complete by release should be documented as known limitations. M3 items are quality-of-life and can be addressed in patch releases (v0.1.1, v0.1.2).

---

## What v0.1 Does NOT Include

These are explicitly deferred to v0.2 or later:

- **Memory consolidation** (full implementation) — deferred; v0.1 disables it with a clear message
- **Cloud sync or multi-device** — out of scope; Yaade is local-first
- **Web UI** — TUI only for v0.1
- **Memory versioning / history** — deferred
- **Export/import** (JSON, CSV) — deferred
- **Undo for deletions** — deferred (nice to have but not blocking)
- **Linux desktop notifications** — deferred
- **Memory linking / graph view** — deferred

---

## v0.2 Preview (Post-v0.1 Backlog)

| Feature | Description |
|---|---|
| Full consolidation | Create a merged memory from a group |
| Model hot-swap | Switch embedding model without re-indexing |
| Database migration | Re-embed all memories when model changes |
| Export / Import | JSON export and import for backup |
| Undo deletion | 30-second grace period after delete |
| Memory versioning | Track edit history per memory |
| Web UI | Optional browser-based alternative to TUI |
