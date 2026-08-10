# System Design — RCI Code Equivalence Platform

## Design Goals

1. **Offline-first** — All features work without internet access
2. **Security-first** — Confidential source code never leaves the machine
3. **Correctness over claims** — No feature is implemented as a facade; limitations are documented
4. **Modular** — Each engine (analysis, comparison, gap detection, execution) is independently testable
5. **Engineer UX** — Clean, information-dense UI; no unnecessary animations or fake metrics

## Key Design Decisions

### Why FastAPI + React instead of Electron?

Electron bundles a full Chromium browser (~150MB). For Phase 1, a simpler approach:
- FastAPI backend on `localhost:8000`
- React frontend on `localhost:5173` (Vite dev) or served by FastAPI in production
- All communication stays on loopback — zero network exposure

This can be wrapped in Electron or Tauri in Phase 15 if a single-executable installer is needed.

### Why SQLite?

- Zero configuration, zero network
- Async access via `aiosqlite`
- Entire database is a single `.db` file (easy backup, easy deletion)
- Source code is **never** stored — only metadata

### Why Regex Parser in Phase 1?

`tree-sitter` and `fparser2` are the correct long-term parsers but require:
- `tree-sitter`: C extension compilation (tree-sitter-c wheel)
- `fparser2`: More complex integration and testing

The regex-based Phase 1 parser:
- Works immediately with zero native dependencies
- Handles the demo examples correctly
- Is clearly labeled `parser_used="regex-structural"` in all IR output
- Makes Phase 3 upgrade path explicit

### Why No LLM in Phase 1?

The specification requires the system to work without any local AI model installed.
The gap detection and comparison engines use deterministic rule-based reasoning.
An `OllamaProvider` interface is defined but not wired up until Phase 6+.

### IR Design: Why Normalize Array Indices?

C uses 0-based indexing; Fortran uses 1-based indexing by default.

Without normalization, every array access in a matched pair would appear as a
difference. The IR normalizes all indices to 0-based logical offsets **before comparison**.
The original base index (`original_base_index=1` for Fortran) is preserved for gap reports.

### Confidence Scores

Every gap has a `confidence` score (0.0–1.0).

Phase 1 scores are based on deterministic heuristics:
- `1.0` = definitely true (e.g., IMPLICIT NONE present/absent)
- `0.85–0.95` = high confidence from structural analysis
- `0.7–0.85` = moderate confidence, heuristic-based
- `< 0.7` = low confidence, manual review required

In Phase 6+, scores may be updated by the optional local AI module.

## API Design

All endpoints are prefixed `/api/v1/`.

### REST Conventions

| Method | Pattern | Meaning |
|--------|---------|---------|
| GET | `/api/v1/health` | Liveness probe |
| GET | `/api/v1/status` | Application status |
| GET | `/api/v1/system-info` | Diagnostics |
| POST | `/api/v1/analysis/upload` | Upload + analyze |
| GET | `/api/v1/analysis/` | List sessions |
| GET | `/api/v1/analysis/{id}` | Get session |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/` | List projects |

### Error Responses

All errors return structured JSON:

```json
{
  "error": "Analysis failed",
  "detail": "Specific error message",
  "session_id": "uuid",
  "offline": true
}
```

Never return raw stack traces to the frontend in production mode.
