# RCI Code Equivalence Platform

> **Offline C ↔ Fortran Code Analysis and Equivalence Verification Platform**

A research-grade desktop/web-local application that analyzes equivalent C and Fortran
implementations of the same computational algorithm, compares them structurally and
semantically, and verifies numerical equivalence through real local execution.

**Key principle:** The system operates **completely offline** — no internet access required,
no external APIs, no cloud storage, no telemetry.

---

## Features (Phase 1)

- ✅ **Source ingestion** — Upload C (`.c`) and Fortran (`.f90`) files
- ✅ **Structural analysis** — Functions, parameters, types, LOC, cyclomatic complexity
- ✅ **Common IR** — Language-independent intermediate representation
- ✅ **Comparison engine** — Function matching by name similarity (Levenshtein)
- ✅ **Gap detection** — 18 gap categories with severity, confidence, and resolution
- ✅ **Compiler detection** — Auto-detects GCC, Clang, GFortran on PATH and MSYS2 paths
- ✅ **System diagnostics** — Real OS, memory, disk, Python, Node.js status
- ✅ **Professional dashboard** — Engineering-grade dark-theme UI
- ✅ **Security sandbox** — Pattern scanning, size validation, source-code log redaction
- ✅ **Offline-first** — All 7 analysis steps work without internet

## Roadmap

| Phase | Status | Feature |
|-------|--------|---------|
| 1  | ✅ Done | Repository, architecture, backend skeleton, frontend dashboard |
| 2  | Planned | Monaco code editor, file upload UI polish |
| 3  | Planned | tree-sitter (C) + fparser2 (Fortran) full AST parsers |
| 4  | Planned | Deep IR generation from ASTs |
| 5  | Planned | Semantic comparison, control-flow graph diff |
| 6  | Planned | Gap management console, diff viewer |
| 7  | Planned | Patch recommendation, human approval workflow |
| 8  | Planned | Compiler adapter, safe execution engine |
| 9  | Planned | Test-input generation, same-input guarantee |
| 10 | Planned | Output capture, normalization, numerical comparison |
| 11 | Planned | Chart.js + Matplotlib visualizations from real data |
| 12 | Planned | PDF/HTML/JSON/CSV report generation |
| 13 | Planned | Security hardening |
| 14 | Planned | Full automated test suite |
| 15 | Planned | Offline packaging (Electron or installer) |
| 16 | Planned | Final demo preparation |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **GCC + GFortran** (optional for Phase 1, required for Phase 8+ execution)
  - Windows: Install via [MSYS2](https://www.msys2.org/) → `pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-gcc-fortran`
  - Linux: `sudo apt install gcc gfortran`

---

## Installation

### 1. Clone / open the project

```powershell
cd d:\Projects\rci-code-equivalence-platform
```

### 2. Set up the Python backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Set up the frontend

```powershell
cd ..\frontend
npm install
```

### 4. Configure (optional)

```powershell
cd ..
copy .env.example .env
# Edit .env to set compiler paths, timeouts, etc.
```

---

## Running Locally

### Backend (Terminal 1)

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs available at: http://127.0.0.1:8000/api/docs

### Frontend (Terminal 2)

```powershell
cd frontend
npm run dev
```

Dashboard available at: http://127.0.0.1:5173

---

## Running Tests

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest -v
```

---

## Quick Demo

Upload the included demo files:

| Concept | C File | Fortran File |
|---------|--------|--------------|
| Projectile motion | `examples/c/projectile.c` | `examples/fortran/projectile.f90` |
| Quadratic solver (with intentional gap) | `examples/c/quadratic.c` | `examples/fortran/quadratic.f90` |
| Vector magnitude | `examples/c/vector_magnitude.c` | `examples/fortran/vector_magnitude.f90` |

The quadratic solver demo has an intentional precision mismatch (C uses `double`,
Fortran uses `REAL` for the discriminant) to demonstrate the gap detector.

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design,
data flow diagrams, and component descriptions.

## Security

See [docs/security.md](docs/security.md) for the security model, threat analysis,
and enforcement mechanisms.

---

## Limitations (Phase 1)

- **C parser**: Regex-based structural extraction. Does not handle all C99/C11 constructs.
  Will be upgraded to `tree-sitter` in Phase 3.
- **Fortran parser**: Regex-based. Does not handle Fortran 77 fixed-form or COMMON blocks.
  Will be upgraded to `fparser2` in Phase 3.
- **Execution**: Compilation and execution are not available until Phase 8.
- **Visualization**: Charts are not available until Phase 11.
- **Reports**: Export is not available until Phase 12.
- **Patch application**: Diff viewer and human approval workflow are Phase 7.

These are **correctly documented limitations**, not hidden gaps.

---

## Security Policy

This platform is designed for use with **confidential source code**:

- No internet required at runtime
- No external APIs called
- Source code is never stored in the database
- Source code is never written to logs
- All subprocess execution uses isolated temp directories
- CORS is restricted to localhost origins only

See [SECURITY.md](docs/security.md) for the full security model.
