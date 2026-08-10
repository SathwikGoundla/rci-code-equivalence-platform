"""
Tests for compiler detection service.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from app.services.compiler_detection import (
    detect_compiler,
    detect_all_compilers,
    CompilerStatus,
    CompilerInfo,
)


def test_detect_nonexistent_compiler():
    """A compiler that doesn't exist should return NOT_FOUND status."""
    info = detect_compiler(
        name="__nonexistent_compiler_xyz__",
        language="C",
    )
    assert info.status == CompilerStatus.NOT_FOUND
    assert info.path is None
    assert info.version is None


def test_detect_compiler_with_invalid_override():
    """A non-existent override path should return ERROR status."""
    info = detect_compiler(
        name="gcc",
        language="C",
        override_path="/nonexistent/path/to/gcc",
    )
    assert info.status == CompilerStatus.ERROR
    assert info.error is not None


def test_compiler_info_fields():
    """CompilerInfo dataclass has all required fields."""
    info = CompilerInfo(
        name="gcc",
        language="C",
        status=CompilerStatus.DETECTED,
        path="/usr/bin/gcc",
        version="13.2.0",
        version_string="gcc (GCC) 13.2.0",
    )
    assert info.name == "gcc"
    assert info.language == "C"
    assert info.status == CompilerStatus.DETECTED
    assert info.version == "13.2.0"


def test_detect_all_compilers_returns_result():
    """detect_all_compilers always returns a CompilerDetectionResult."""
    result = detect_all_compilers()
    assert result is not None
    assert isinstance(result.c_compilers, list)
    assert isinstance(result.fortran_compilers, list)
    assert len(result.c_compilers) > 0
    assert len(result.fortran_compilers) > 0


def test_detection_result_properties():
    """has_c_compiler and has_fortran_compiler reflect actual detection status."""
    result = detect_all_compilers()
    # These are boolean properties — just verify they don't throw
    _ = result.has_c_compiler
    _ = result.has_fortran_compiler
    _ = result.preferred_c_compiler
    _ = result.preferred_fortran_compiler


@patch("app.services.compiler_detection.shutil.which", return_value="/usr/bin/gcc")
@patch("app.services.compiler_detection._get_version", return_value=("13.2.0", "gcc (GCC) 13.2.0"))
def test_detect_compiler_with_mocked_path(mock_version, mock_which):
    """With a mocked path, compiler should be detected as DETECTED."""
    import os
    with patch("os.path.isfile", return_value=True):
        info = detect_compiler("gcc", "C")
    assert info.status == CompilerStatus.DETECTED
    assert info.version == "13.2.0"
