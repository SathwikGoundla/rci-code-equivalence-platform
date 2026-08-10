"""
Execution Engine

Safely compiles and executes C and Fortran programs in isolated temporary directories.

SECURITY REQUIREMENTS (enforced):
- Never use shell=True
- Always run with a timeout
- Always clean up temporary files after execution
- Strip environment variables before child process execution
- Run in a dedicated temp directory, never the project directory

Phase 1: Framework and interface defined. Compilation/execution implemented in Phase 8.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    NOT_AVAILABLE = "not_available"


@dataclass
class CompilationResult:
    success: bool
    executable_path: Optional[str]
    stdout: str
    stderr: str
    return_code: int
    language: str
    compiler_used: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    stdin_used: str = ""
    timed_out: bool = False


# ── Safe Environment ──────────────────────────────────────────────────────────
_SAFE_ENV_KEYS = {"PATH", "TEMP", "TMP", "TMPDIR", "SystemRoot", "COMSPEC"}


def _safe_environment() -> dict[str, str]:
    """Strip all environment variables except a minimal safe set."""
    return {
        k: v for k, v in os.environ.items()
        if k in _SAFE_ENV_KEYS
    }


class ExecutionEngine:
    """
    Manages compilation and execution of C and Fortran programs.

    Phase 1: Framework established, compilation/execution wired up in Phase 8.
    """

    def __init__(self, timeout_seconds: int = 30, tmp_base: Optional[str] = None):
        self.timeout_seconds = timeout_seconds
        self.tmp_base = tmp_base

    def _compile(
        self,
        source_path: Path,
        compiler_path: str,
        output_path: Path,
        extra_flags: List[str],
        language: str,
    ) -> CompilationResult:
        """
        Compile a source file using the specified compiler.
        Never uses shell=True.
        """
        cmd = [compiler_path, str(source_path), "-o", str(output_path)] + extra_flags

        logger.info("Compiling %s: %s", language, " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                env=_safe_environment(),
                cwd=str(output_path.parent),
            )
            success = result.returncode == 0
            return CompilationResult(
                success=success,
                executable_path=str(output_path) if success else None,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                language=language,
                compiler_used=compiler_path,
                errors=[
                    line for line in result.stderr.splitlines()
                    if "error:" in line.lower()
                ],
                warnings=[
                    line for line in result.stderr.splitlines()
                    if "warning:" in line.lower()
                ],
            )
        except subprocess.TimeoutExpired:
            return CompilationResult(
                success=False,
                executable_path=None,
                stdout="",
                stderr="Compilation timed out after 60 seconds.",
                return_code=-1,
                language=language,
                compiler_used=compiler_path,
                errors=["Compilation timeout"],
            )
        except FileNotFoundError:
            return CompilationResult(
                success=False,
                executable_path=None,
                stdout="",
                stderr=f"Compiler not found: {compiler_path}",
                return_code=-1,
                language=language,
                compiler_used=compiler_path,
                errors=[f"Compiler not found: {compiler_path}"],
            )

    def execute(
        self,
        executable_path: str,
        stdin_input: str = "",
    ) -> ExecutionResult:
        """
        Execute a compiled binary with the given stdin.
        Enforces timeout and safe environment.
        """
        try:
            start_time = time.perf_counter()
            result = subprocess.run(
                [executable_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=_safe_environment(),
                cwd=str(Path(executable_path).parent),
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            status = (
                ExecutionStatus.SUCCESS
                if result.returncode == 0
                else ExecutionStatus.RUNTIME_ERROR
            )

            return ExecutionResult(
                status=status,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time_ms=round(elapsed_ms, 2),
                stdin_used=stdin_input,
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr=f"Execution timed out after {self.timeout_seconds} seconds.",
                exit_code=-1,
                execution_time_ms=self.timeout_seconds * 1000.0,
                stdin_used=stdin_input,
                timed_out=True,
            )
        except Exception as exc:
            return ExecutionResult(
                status=ExecutionStatus.RUNTIME_ERROR,
                stdout="",
                stderr=str(exc),
                exit_code=-1,
                execution_time_ms=0.0,
                stdin_used=stdin_input,
            )

    def compile_and_run_c(
        self,
        source_code: str,
        compiler_path: str,
        stdin_input: str = "",
        flags: Optional[List[str]] = None,
    ) -> tuple[CompilationResult, Optional[ExecutionResult]]:
        """Compile C source and execute it. Returns (CompilationResult, ExecutionResult|None)."""
        flags = flags or ["-Wall", "-Wextra", "-lm", "-O0"]

        with tempfile.TemporaryDirectory(prefix="rci_c_", dir=self.tmp_base) as tmpdir:
            src_path = Path(tmpdir) / "program.c"
            exe_path = Path(tmpdir) / "program.exe"

            src_path.write_text(source_code, encoding="utf-8")
            compile_result = self._compile(src_path, compiler_path, exe_path, flags, "C")

            if not compile_result.success:
                return compile_result, None

            exec_result = self.execute(str(exe_path), stdin_input)
            return compile_result, exec_result

    def compile_and_run_fortran(
        self,
        source_code: str,
        compiler_path: str,
        stdin_input: str = "",
        flags: Optional[List[str]] = None,
    ) -> tuple[CompilationResult, Optional[ExecutionResult]]:
        """Compile Fortran source and execute it."""
        flags = flags or ["-Wall", "-O0"]

        with tempfile.TemporaryDirectory(prefix="rci_f_", dir=self.tmp_base) as tmpdir:
            src_path = Path(tmpdir) / "program.f90"
            exe_path = Path(tmpdir) / "program.exe"

            src_path.write_text(source_code, encoding="utf-8")
            compile_result = self._compile(src_path, compiler_path, exe_path, flags, "Fortran")

            if not compile_result.success:
                return compile_result, None

            exec_result = self.execute(str(exe_path), stdin_input)
            return compile_result, exec_result
