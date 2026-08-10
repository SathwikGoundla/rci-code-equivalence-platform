"""
Security Sandbox

Validates and sanitizes inputs before execution.
Enforces security policies for source code handling.

SECURITY INVARIANTS (must never be violated):
1. No source code content is ever written to application logs
2. No source code is transmitted to any external service
3. All child processes run with stripped environment variables
4. Temporary files are always deleted after use
5. Source file size is validated before any processing
6. shell=True is NEVER used in subprocess calls
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import List, Tuple

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityValidationError(ValueError):
    """Raised when source code fails security validation."""
    pass


# ── Dangerous patterns that should never be executed ──────────────────────────
# These are heuristics only — do NOT rely solely on this for production security
_DANGEROUS_C_PATTERNS: List[re.Pattern] = [
    re.compile(r'\bsystem\s*\(', re.IGNORECASE),
    re.compile(r'\bexec[vl]p?\s*\(', re.IGNORECASE),
    re.compile(r'\bpopen\s*\(', re.IGNORECASE),
    re.compile(r'\bfork\s*\(', re.IGNORECASE),
]

_DANGEROUS_FORTRAN_PATTERNS: List[re.Pattern] = [
    re.compile(r'\bCALL\s+SYSTEM\s*\(', re.IGNORECASE),
    re.compile(r'\bEXECUTE_COMMAND_LINE\s*\(', re.IGNORECASE),
]


def validate_c_source(source: str, filename: str = "<unknown>") -> List[str]:
    """
    Validate C source for security concerns.
    Returns a list of warnings (not errors — execution is still allowed with warnings).
    Warnings are shown to the user before execution.
    """
    warnings = []

    for pattern in _DANGEROUS_C_PATTERNS:
        if pattern.search(source):
            warnings.append(
                f"Warning: Source code contains potentially dangerous pattern: "
                f"'{pattern.pattern}'. Review before execution."
            )

    # Log only filename, NEVER source content
    if warnings:
        logger.warning(
            "Security warnings for C file '%s': %d pattern(s) detected",
            filename,
            len(warnings),
        )

    return warnings


def validate_fortran_source(source: str, filename: str = "<unknown>") -> List[str]:
    """
    Validate Fortran source for security concerns.
    """
    warnings = []

    for pattern in _DANGEROUS_FORTRAN_PATTERNS:
        if pattern.search(source):
            warnings.append(
                f"Warning: Source code contains potentially dangerous pattern: "
                f"'{pattern.pattern}'. Review before execution."
            )

    if warnings:
        logger.warning(
            "Security warnings for Fortran file '%s': %d pattern(s) detected",
            filename,
            len(warnings),
        )

    return warnings


def validate_file_size(content: bytes, max_bytes: int, filename: str) -> None:
    """Raises SecurityValidationError if file is too large."""
    if len(content) > max_bytes:
        raise SecurityValidationError(
            f"File '{filename}' exceeds maximum allowed size "
            f"({len(content)} > {max_bytes} bytes)."
        )
