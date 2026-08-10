# SECURITY.md — RCI Code Equivalence Platform

## Security Model

This platform is designed for use with **confidential scientific and engineering source code**.
All security decisions prioritize data confidentiality and offline operation.

---

## Core Security Invariants

These invariants are enforced in code and must **never** be violated:

| # | Invariant | Where Enforced |
|---|-----------|----------------|
| 1 | No source code content is ever written to application logs | `SecurityFilter` in `utils/logging.py` |
| 2 | No source code is transmitted to any external service | CORS restricted to localhost only (`main.py`) |
| 3 | All child processes run with stripped environment variables | `security/sandbox.py` `_safe_environment()` |
| 4 | Temporary files are always deleted after execution | `tempfile.TemporaryDirectory` context manager |
| 5 | Source file size is validated before any processing | `security/sandbox.py` `validate_file_size()` |
| 6 | `shell=True` is NEVER used in subprocess calls | All `subprocess.run()` calls use list arguments |
| 7 | No cloud database — SQLite only | `database.py` — SQLite, no network socket |
| 8 | No telemetry, no analytics, no error reporting to external services | No such code exists in this codebase |
| 9 | CORS allows only localhost origins | `main.py` CORS middleware configuration |
| 10 | Child processes run with hard timeouts | `execution/engine.py` timeout enforcement |

---

## Threat Model

### In Scope

- **Confidential source code exposure**: Source content is never logged, never stored in DB, never transmitted externally.
- **Malicious source code execution**: Patterns like `system()`, `popen()`, `EXECUTE_COMMAND_LINE` are flagged before execution. User must acknowledge warnings.
- **Process escaping**: Subprocess isolation via stripped environment variables and temp directories.
- **Log exposure**: Source code is redacted from all log entries.

### Out of Scope (Developer Environment)

- **Multi-user authentication**: This is a single-user local desktop tool. No authentication system is implemented.
- **Network-level security**: The server binds to `127.0.0.1` only. No external network exposure.
- **Memory dumps**: OS-level memory forensics are outside scope.

---

## What Gets Stored in the Database

The SQLite database stores **only metadata**, never source code:

```
analysis_sessions:
  - id, status, c_filename, fortran_filename     ← filenames only, no content
  - c_file_size, fortran_file_size               ← sizes only
  - c_analysis_json                              ← parsed IR metadata (functions, types)
  - fortran_analysis_json                        ← parsed IR metadata
  - gaps_detected, high_severity_gaps            ← counts
```

Source code bytes are **never written to disk** except in isolated temporary directories during compilation, which are automatically cleaned up.

---

## Subprocess Execution Security

When executing compiled programs:

1. Compiler and executable paths are validated to be real files.
2. `subprocess.run()` always uses **list arguments**, never shell strings.
3. The child process environment is stripped to only: `PATH, TEMP, TMP, TMPDIR, SystemRoot, COMSPEC`.
4. A hard **timeout** (default 30s, configurable) kills the process if exceeded.
5. The compiled executable is written to a **temporary directory** that is deleted after execution.
6. No network access is possible from within the execution sandbox (OS-enforced).

---

## Log Redaction

Set `REDACT_SOURCE_CODE_IN_LOGS=true` (default) to enable the `SecurityFilter`.

The filter will redact messages that:
- Are longer than 500 characters AND
- Contain `#include`, `PROGRAM `, or `SUBROUTINE `

This prevents accidental logging of source file content if a developer adds a debug statement.

---

## Offline Verification

The application has **no runtime internet dependency**. To verify:

```powershell
# Start with Wi-Fi off
# The application must still start and function fully
uvicorn app.main:app
```

The CORS configuration explicitly limits origins to `localhost` and `127.0.0.1`. Any attempt to call the API from a non-localhost origin will be rejected.

---

## Reporting Security Issues

This is an internal research platform. Report security concerns to your project lead directly.
