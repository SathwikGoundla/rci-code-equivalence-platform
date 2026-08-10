"""
Tests for IR models, C analyzer, Fortran analyzer, and comparison engine.
"""

import pytest

from app.ir.models import (
    CanonicalType,
    FunctionIR,
    ProgramIR,
    ProgramMetadata,
    VariableIR,
)
from app.analyzers.c.analyzer import analyze_c_source
from app.analyzers.fortran.analyzer import analyze_fortran_source
from app.comparison.engine import compare_programs, _name_similarity
from app.gap_detection.engine import GapDetectionEngine, GapCategory, GapSeverity


# ── IR Model Tests ─────────────────────────────────────────────────────────────

def test_program_ir_function_names():
    ir = ProgramIR(
        metadata=ProgramMetadata(filename="test.c", source_language="C"),
        functions=[
            FunctionIR(name="foo", source_language="C"),
            FunctionIR(name="bar", source_language="C"),
        ],
    )
    assert ir.function_names == ["foo", "bar"]
    assert ir.function_count == 2


def test_program_ir_get_function():
    fn = FunctionIR(name="calculate", source_language="C")
    ir = ProgramIR(
        metadata=ProgramMetadata(filename="test.c", source_language="C"),
        functions=[fn],
    )
    assert ir.get_function("calculate") is fn
    assert ir.get_function("nonexistent") is None


def test_variable_ir_array():
    var = VariableIR(
        name="matrix",
        canonical_type=CanonicalType.FLOAT64,
        is_array=True,
        array_dimensions=[(0, 9), (0, 9)],
    )
    assert var.is_array is True
    assert len(var.array_dimensions) == 2


# ── C Analyzer Tests ───────────────────────────────────────────────────────────

C_SAMPLE = """
#include <stdio.h>
#include <math.h>

#define PI 3.14159265358979

double calculate(double x) {
    return x * x + 2.0;
}

int main(void) {
    double result = calculate(5.0);
    printf("Result = %f\\n", result);
    return 0;
}
"""

def test_c_analyzer_finds_functions():
    ir = analyze_c_source(C_SAMPLE, "test.c")
    assert ir.metadata.source_language == "C"
    assert len(ir.functions) >= 1
    fn_names = [f.name for f in ir.functions]
    assert "calculate" in fn_names or "main" in fn_names


def test_c_analyzer_detects_includes():
    ir = analyze_c_source(C_SAMPLE, "test.c")
    assert "stdio.h" in ir.includes or "math.h" in ir.includes


def test_c_analyzer_detects_defines():
    ir = analyze_c_source(C_SAMPLE, "test.c")
    const_names = [c.name for c in ir.constants]
    assert "PI" in const_names


def test_c_analyzer_counts_lines():
    ir = analyze_c_source(C_SAMPLE, "test.c")
    assert ir.metadata.total_lines > 0
    assert ir.metadata.total_loc > 0


# ── Fortran Analyzer Tests ─────────────────────────────────────────────────────

FORTRAN_SAMPLE = """
PROGRAM ProjectileMotion
    IMPLICIT NONE
    DOUBLE PRECISION :: v0, angle, g, t, x, y
    PARAMETER (g = 9.81d0)

    v0 = 100.0d0
    angle = 45.0d0

    t = 2.0d0 * v0 * SIN(angle) / g
    x = v0 * COS(angle) * t
    y = 0.0d0

    WRITE(*,*) 'Range =', x
END PROGRAM ProjectileMotion

FUNCTION calculate(x)
    IMPLICIT NONE
    DOUBLE PRECISION :: x, calculate
    calculate = x * x + 2.0d0
END FUNCTION calculate
"""

def test_fortran_analyzer_finds_program():
    ir = analyze_fortran_source(FORTRAN_SAMPLE, "test.f90")
    assert ir.metadata.source_language == "Fortran"
    fn_names = [f.name for f in ir.functions]
    assert "ProjectileMotion" in fn_names or "calculate" in fn_names


def test_fortran_analyzer_detects_io():
    ir = analyze_fortran_source(FORTRAN_SAMPLE, "test.f90")
    prog_unit = next((f for f in ir.functions if f.name == "ProjectileMotion"), None)
    if prog_unit:
        assert prog_unit.has_io is True


def test_fortran_analyzer_detects_implicit_none():
    ir = analyze_fortran_source(FORTRAN_SAMPLE, "test.f90")
    prog_unit = next((f for f in ir.functions if f.name == "ProjectileMotion"), None)
    if prog_unit:
        assert prog_unit.has_implicit_none is True


# ── Comparison Engine Tests ────────────────────────────────────────────────────

def test_name_similarity_exact():
    assert _name_similarity("calculate", "calculate") == 1.0


def test_name_similarity_partial():
    score = _name_similarity("calculate", "calc")
    assert 0.5 <= score <= 1.0


def test_name_similarity_different():
    score = _name_similarity("calculate", "xyzabc")
    assert score < 0.5


def test_compare_programs_identical_names():
    c_ir = analyze_c_source(C_SAMPLE, "test.c")
    f_ir = analyze_fortran_source(FORTRAN_SAMPLE, "test.f90")
    result = compare_programs(c_ir, f_ir)
    assert result is not None
    assert 0.0 <= result.structural_score <= 1.0
    assert isinstance(result.c_only_functions, list)
    assert isinstance(result.fortran_only_functions, list)


# ── Gap Detection Tests ────────────────────────────────────────────────────────

def test_gap_detection_missing_implicit_none():
    """Fortran without IMPLICIT NONE should trigger an initialization_mismatch gap."""
    fortran_no_implicit = """
SUBROUTINE testSub(x)
    REAL :: x
    x = x * 2.0
END SUBROUTINE testSub
"""
    c_ir = analyze_c_source("double testSub(double x) { return x * 2.0; }", "test.c")
    f_ir = analyze_fortran_source(fortran_no_implicit, "test.f90")
    comparison = compare_programs(c_ir, f_ir)

    engine = GapDetectionEngine()
    gaps = engine.detect(comparison)

    init_gaps = [g for g in gaps if g.category == GapCategory.INITIALIZATION_MISMATCH]
    assert len(init_gaps) > 0
    assert init_gaps[0].confidence > 0.9


def test_gap_detection_produces_ids():
    """Every gap must have a unique sequential GAP-XXX ID."""
    c_ir = analyze_c_source(C_SAMPLE, "test.c")
    f_ir = analyze_fortran_source(FORTRAN_SAMPLE, "test.f90")
    comparison = compare_programs(c_ir, f_ir)

    engine = GapDetectionEngine()
    gaps = engine.detect(comparison)

    for gap in gaps:
        assert gap.gap_id.startswith("GAP-")
        assert len(gap.gap_id) == 7  # "GAP-XXX"


def test_gap_to_dict_has_required_fields():
    """GapReport.to_dict() must contain all required fields."""
    c_ir = analyze_c_source(C_SAMPLE, "test.c")
    f_ir = analyze_fortran_source(FORTRAN_SAMPLE, "test.f90")
    comparison = compare_programs(c_ir, f_ir)

    engine = GapDetectionEngine()
    gaps = engine.detect(comparison)

    required = {"id", "gap_id", "category", "severity", "explanation", "confidence", "suggested_resolution"}
    for gap in gaps:
        d = gap.to_dict()
        for key in required:
            assert key in d, f"Missing key '{key}' in gap dict"
