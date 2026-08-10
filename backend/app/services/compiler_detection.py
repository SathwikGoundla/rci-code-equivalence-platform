"""
Compiler Detection Service

Detects locally installed C and Fortran compilers by probing common paths
and querying version information. Never relies on internet access.

Supports:
    C:       gcc, clang
    Fortran: gfortran

On Windows, checks standard MSYS2/MinGW locations in addition to PATH.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class CompilerStatus(str, Enum):
    DETECTED = "detected"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass
class CompilerInfo:
    name: str
    language: str
    status: CompilerStatus
    path: Optional[str] = None
    version: Optional[str] = None
    version_string: Optional[str] = None
    error: Optional[str] = None


# ── Windows-specific search paths ─────────────────────────────────────────────
_WINDOWS_EXTRA_PATHS: List[str] = [
    r"C:\msys64\mingw64\bin",
    r"C:\msys64\usr\bin",
    r"C:\msys64\mingw32\bin",
    r"C:\MinGW\bin",
    r"C:\TDM-GCC-64\bin",
    r"C:\Program Files\LLVM\bin",
    r"C:\Program Files (x86)\LLVM\bin",
]


def _find_executable(name: str) -> Optional[str]:
    """
    Find an executable by name, checking PATH and Windows-specific locations.
    Returns the absolute path or None.
    """
    # First try shutil.which (respects PATH)
    path = shutil.which(name)
    if path:
        return path

    # Windows fallback: check common installation directories
    if sys.platform == "win32":
        for base in _WINDOWS_EXTRA_PATHS:
            candidate = os.path.join(base, name + ".exe")
            if os.path.isfile(candidate):
                return candidate

    return None


def _get_version(executable_path: str) -> tuple[Optional[str], Optional[str]]:
    """
    Run `<compiler> --version` and parse the output.
    Returns (short_version, full_version_string).
    """
    try:
        result = subprocess.run(
            [executable_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            env={},  # clean environment
        )
        version_string = (result.stdout or result.stderr).strip()
        first_line = version_string.splitlines()[0] if version_string else ""

        # Extract version number (e.g., "13.2.0" from "gcc (GCC) 13.2.0")
        import re
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
        short_version = match.group(1) if match else None

        return short_version, first_line
    except subprocess.TimeoutExpired:
        return None, "Version query timed out"
    except Exception as exc:
        return None, str(exc)


def detect_compiler(name: str, language: str, override_path: str = "") -> CompilerInfo:
    """
    Detect a single compiler. Uses override_path if provided.
    """
    exe_path = override_path.strip() if override_path else None

    if not exe_path:
        exe_path = _find_executable(name)

    if not exe_path:
        logger.info("Compiler '%s' not found in PATH or known locations", name)
        return CompilerInfo(
            name=name,
            language=language,
            status=CompilerStatus.NOT_FOUND,
        )

    if not os.path.isfile(exe_path):
        logger.warning("Configured compiler path does not exist: %s", exe_path)
        return CompilerInfo(
            name=name,
            language=language,
            status=CompilerStatus.ERROR,
            path=exe_path,
            error=f"File not found: {exe_path}",
        )

    short_version, version_string = _get_version(exe_path)

    logger.info(
        "Compiler '%s' detected at '%s' (version: %s)",
        name,
        exe_path,
        short_version or "unknown",
    )

    return CompilerInfo(
        name=name,
        language=language,
        status=CompilerStatus.DETECTED,
        path=exe_path,
        version=short_version,
        version_string=version_string,
    )


@dataclass
class CompilerDetectionResult:
    c_compilers: List[CompilerInfo] = field(default_factory=list)
    fortran_compilers: List[CompilerInfo] = field(default_factory=list)

    @property
    def has_c_compiler(self) -> bool:
        return any(c.status == CompilerStatus.DETECTED for c in self.c_compilers)

    @property
    def has_fortran_compiler(self) -> bool:
        return any(c.status == CompilerStatus.DETECTED for c in self.fortran_compilers)

    @property
    def preferred_c_compiler(self) -> Optional[CompilerInfo]:
        return next(
            (c for c in self.c_compilers if c.status == CompilerStatus.DETECTED), None
        )

    @property
    def preferred_fortran_compiler(self) -> Optional[CompilerInfo]:
        return next(
            (c for c in self.fortran_compilers if c.status == CompilerStatus.DETECTED),
            None,
        )


def detect_all_compilers(
    c_override: str = "",
    fortran_override: str = "",
) -> CompilerDetectionResult:
    """
    Detect all supported C and Fortran compilers.
    Called at startup and exposed via the /system-info endpoint.
    """
    from app.config import get_settings
    settings = get_settings()

    c_override = c_override or settings.c_compiler_path
    fortran_override = fortran_override or settings.fortran_compiler_path

    result = CompilerDetectionResult()

    # C compilers (tried in preference order)
    for c_name in ["gcc", "clang", "cc"]:
        # For the first one, apply the override; for others, auto-detect
        override = c_override if c_name == "gcc" else ""
        info = detect_compiler(c_name, "C", override_path=override)
        result.c_compilers.append(info)
        if c_override and info.status == CompilerStatus.DETECTED:
            break  # override was specified and worked

    # Fortran compilers
    for f_name in ["gfortran"]:
        info = detect_compiler(f_name, "Fortran", override_path=fortran_override)
        result.fortran_compilers.append(info)

    return result
