# User Guide — RCI Code Equivalence Platform

## Getting Started

### 1. Start the Application

Open **two terminals**:

**Terminal 1 — Backend:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Open: http://127.0.0.1:5173

---

## Dashboard

The dashboard shows:
- **Compiler Status** — whether GCC and GFortran are detected on your system
- **Platform Metrics** — number of sessions, detected gaps, high-severity gaps
- **System Status** — OS, memory, disk, uptime, offline confirmation
- **Recent Analyses** — table of the last 8 sessions with gap counts
- **Pipeline Status** — which pipeline stages are implemented (Phase 1 vs future)

If you see "Backend connection error", make sure the FastAPI server is running.

---

## Code Analysis Page

### Uploading Files

1. Click the **C Source File** card → select a `.c` file
2. Click the **Fortran Source File** card → select a `.f90` file
3. Click **Analyze Both Files**

### Reading Results

**Structural Comparison:**
- `Structural Score` — percentage of matched function pairs (higher = more structurally similar)
- `Matched Pairs` — C functions that have a Fortran counterpart
- `C Only` — C functions with no Fortran equivalent
- `Fortran Only` — Fortran units with no C equivalent

**Function Tables:**
- `LOC` — lines of code (non-blank, non-comment)
- `CC` — cyclomatic complexity (1 = simple, >10 = complex)
- `LOOP` — contains loops
- `IF` — contains conditional branches
- `I/O` — contains input/output operations
- `IMPL.NONE` — Fortran unit has IMPLICIT NONE

**Gap Table:**
- Click any gap row to expand the full explanation, evidence, and suggested resolution
- Confidence: percentage certainty from deterministic analysis
- Status: `open` = not yet reviewed

---

## System Diagnostics Page

Shows comprehensive real-time system information:
- **OS** — name, version, architecture, CPU count, memory
- **Python** — version, executable path, Node.js version
- **C Compilers** — detection status, version, full path
- **Fortran Compilers** — detection status, version, full path
- **Storage** — disk usage with visual bar
- **Security** — confirms all security invariants (no internet, no external APIs)

### Installing Missing Compilers (Windows)

If compilers show "Not Found":

1. Install [MSYS2](https://www.msys2.org/)
2. Open MSYS2 MinGW 64-bit terminal
3. Run:
   ```bash
   pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-gcc-fortran
   ```
4. Add `C:\msys64\mingw64\bin` to your Windows PATH
5. Restart the backend and refresh the Diagnostics page

---

## Demo Files

Use the included demo files to try the platform immediately:

| Example | Gap Demo |
|---------|----------|
| `examples/c/projectile.c` + `examples/fortran/projectile.f90` | Equivalent implementations — low gap count |
| `examples/c/quadratic.c` + `examples/fortran/quadratic.f90` | **Intentional precision gap** — demonstrates PRECISION_MISMATCH |
| `examples/c/vector_magnitude.c` + `examples/fortran/vector_magnitude.f90` | Array indexing difference |

---

## Settings Page

Configure:
- **Absolute tolerance (atol)** — for numerical output comparison (Phase 10)
- **Relative tolerance (rtol)** — for numerical output comparison (Phase 10)
- **Execution timeout** — seconds before killing a hung process
- **Compiler paths** — override auto-detection with specific paths

---

## Limitations (Phase 1)

| Feature | Status |
|---------|--------|
| C parser | Regex-based — may miss complex macros or function pointer types |
| Fortran parser | Regex-based — may miss Fortran 77 fixed-form, COMMON blocks |
| Compilation & execution | Not yet available (Phase 8) |
| Visualization | Not yet available (Phase 11) |
| Report export | Not yet available (Phase 12) |
| Patch application | Not yet available (Phase 7) |

These are known limitations, not bugs.
