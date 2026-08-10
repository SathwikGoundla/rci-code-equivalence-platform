"""
Gap Detection Engine

Classifies differences between C and Fortran IRs into the 18 gap categories
defined in the system specification. Each gap has a severity, confidence score,
location, explanation, evidence, and suggested resolution.

This engine consumes ComparisonResult and produces a list of Gap objects.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from app.comparison.engine import ComparisonResult, FunctionMatchResult
from app.ir.models import CanonicalType, ProgramIR

logger = logging.getLogger(__name__)


# ── Gap Categories (all 18 from spec) ─────────────────────────────────────────
class GapCategory(str, Enum):
    MISSING_FUNCTION = "missing_function"
    MISSING_SUBROUTINE = "missing_subroutine"
    MISSING_VARIABLE = "missing_variable"
    MISSING_CONSTANT = "missing_constant"
    MISSING_CALCULATION = "missing_calculation"
    MISSING_BRANCH = "missing_branch"
    MISSING_LOOP = "missing_loop"
    DIFFERENT_LOOP_BOUNDARY = "different_loop_boundary"
    DIFFERENT_ARRAY_DIMENSION = "different_array_dimension"
    DIFFERENT_INPUT_HANDLING = "different_input_handling"
    DIFFERENT_OUTPUT_HANDLING = "different_output_handling"
    TYPE_MISMATCH = "type_mismatch"
    PRECISION_MISMATCH = "precision_mismatch"
    EXPRESSION_MISMATCH = "expression_mismatch"
    FUNCTION_CALL_MISMATCH = "function_call_mismatch"
    INITIALIZATION_MISMATCH = "initialization_mismatch"
    POTENTIAL_NUMERICAL_DISCREPANCY = "potential_numerical_discrepancy"
    UNKNOWN = "unknown"


class GapSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class GapReport:
    """A single detected gap between C and Fortran implementations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gap_id: str = ""         # e.g. "GAP-001"
    category: GapCategory = GapCategory.UNKNOWN
    severity: GapSeverity = GapSeverity.MEDIUM
    source_language: str = "C"
    target_language: str = "Fortran"
    location: str = ""
    explanation: str = ""
    evidence: str = ""
    confidence: float = 0.5
    suggested_resolution: str = ""
    status: str = "open"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gap_id": self.gap_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "location": self.location,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "suggested_resolution": self.suggested_resolution,
            "status": self.status,
        }


# ── Precision risk pairs ───────────────────────────────────────────────────────
_PRECISION_RISK = {
    (CanonicalType.FLOAT32, CanonicalType.FLOAT64),
    (CanonicalType.FLOAT64, CanonicalType.FLOAT32),
    (CanonicalType.FLOAT32, CanonicalType.FLOAT128),
    (CanonicalType.FLOAT128, CanonicalType.FLOAT32),
    (CanonicalType.INT32, CanonicalType.INT64),
    (CanonicalType.INT64, CanonicalType.INT32),
}


class GapDetectionEngine:
    """
    Analyses a ComparisonResult and produces a list of GapReport objects.
    """

    def __init__(self) -> None:
        self._gap_counter = 0

    def _next_id(self) -> str:
        self._gap_counter += 1
        return f"GAP-{self._gap_counter:03d}"

    def detect(self, comparison: ComparisonResult) -> List[GapReport]:
        """Run all gap detectors and return combined list."""
        self._gap_counter = 0
        gaps: List[GapReport] = []

        gaps.extend(self._detect_missing_functions(comparison))
        gaps.extend(self._detect_type_mismatches(comparison))
        gaps.extend(self._detect_precision_issues(comparison))
        gaps.extend(self._detect_io_differences(comparison))
        gaps.extend(self._detect_complexity_gaps(comparison))
        gaps.extend(self._detect_loop_differences(comparison))
        gaps.extend(self._detect_implicit_none(comparison))

        logger.info("Gap detection complete: %d gaps found", len(gaps))
        return gaps

    def _detect_missing_functions(self, comparison: ComparisonResult) -> List[GapReport]:
        gaps = []

        for fn_name in comparison.c_only_functions:
            gaps.append(GapReport(
                gap_id=self._next_id(),
                category=GapCategory.MISSING_FUNCTION,
                severity=GapSeverity.HIGH,
                source_language="C",
                target_language="Fortran",
                location=f"C function: {fn_name}",
                explanation=(
                    f"C function '{fn_name}' has no identifiable counterpart in "
                    f"the Fortran implementation."
                ),
                evidence=f"C defines '{fn_name}'; no Fortran FUNCTION/SUBROUTINE matches.",
                confidence=0.85,
                suggested_resolution=(
                    f"Implement a Fortran FUNCTION or SUBROUTINE named '{fn_name}' "
                    f"(or verify if it exists under a different name)."
                ),
            ))

        for fn_name in comparison.fortran_only_functions:
            gaps.append(GapReport(
                gap_id=self._next_id(),
                category=GapCategory.MISSING_SUBROUTINE,
                severity=GapSeverity.HIGH,
                source_language="Fortran",
                target_language="C",
                location=f"Fortran unit: {fn_name}",
                explanation=(
                    f"Fortran unit '{fn_name}' has no identifiable counterpart in "
                    f"the C implementation."
                ),
                evidence=f"Fortran defines '{fn_name}'; no C function matches.",
                confidence=0.85,
                suggested_resolution=(
                    f"Implement a C function equivalent to Fortran '{fn_name}'."
                ),
            ))

        return gaps

    def _detect_type_mismatches(self, comparison: ComparisonResult) -> List[GapReport]:
        gaps = []

        for match in comparison.function_matches:
            if not (match.c_function and match.fortran_function):
                continue
            if not match.return_type_match:
                c_rt = match.c_function.return_type
                f_rt = match.fortran_function.return_type
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.TYPE_MISMATCH,
                    severity=GapSeverity.MEDIUM,
                    source_language="C",
                    target_language="Fortran",
                    location=(
                        f"C:{match.c_function.name} / "
                        f"Fortran:{match.fortran_function.name}"
                    ),
                    explanation=(
                        f"Return type mismatch between C '{match.c_function.name}' "
                        f"({c_rt.value if c_rt else 'void'}) and Fortran "
                        f"'{match.fortran_function.name}' "
                        f"({f_rt.value if f_rt else 'none'})."
                    ),
                    evidence=f"C return type: {c_rt}; Fortran return type: {f_rt}",
                    confidence=0.9,
                    suggested_resolution=(
                        "Verify that both implementations handle the same numerical "
                        "precision. Consider using DOUBLE PRECISION in Fortran if C uses double."
                    ),
                ))

            if not match.param_count_match:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.MISSING_VARIABLE,
                    severity=GapSeverity.HIGH,
                    source_language="C",
                    target_language="Fortran",
                    location=(
                        f"C:{match.c_function.name} / "
                        f"Fortran:{match.fortran_function.name}"
                    ),
                    explanation=(
                        f"Parameter count mismatch: C has "
                        f"{len(match.c_function.parameters)} parameter(s), "
                        f"Fortran has {len(match.fortran_function.parameters)}."
                    ),
                    evidence="; ".join(match.notes),
                    confidence=0.88,
                    suggested_resolution=(
                        "Ensure both implementations accept the same number of inputs. "
                        "Check if Fortran uses MODULE variables where C uses parameters."
                    ),
                ))

        return gaps

    def _detect_precision_issues(self, comparison: ComparisonResult) -> List[GapReport]:
        gaps = []

        for match in comparison.function_matches:
            if not (match.c_function and match.fortran_function):
                continue

            c_rt = match.c_function.return_type
            f_rt = match.fortran_function.return_type

            if c_rt and f_rt and (c_rt, f_rt) in _PRECISION_RISK:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.PRECISION_MISMATCH,
                    severity=GapSeverity.MEDIUM,
                    source_language="C",
                    target_language="Fortran",
                    location=(
                        f"C:{match.c_function.name} ↔ "
                        f"Fortran:{match.fortran_function.name}"
                    ),
                    explanation=(
                        f"Precision mismatch: C uses {c_rt.value} "
                        f"while Fortran uses {f_rt.value}. "
                        f"This may cause numerical differences in computed results."
                    ),
                    evidence=(
                        f"C return: {c_rt.value}, Fortran return: {f_rt.value}. "
                        f"IEEE 754: float32 has ~7 decimal digits, "
                        f"float64 has ~15 decimal digits of precision."
                    ),
                    confidence=0.91,
                    suggested_resolution=(
                        "Use the same precision in both implementations. "
                        "If C uses 'double', use DOUBLE PRECISION (or REAL(8)) in Fortran."
                    ),
                ))

        return gaps

    def _detect_io_differences(self, comparison: ComparisonResult) -> List[GapReport]:
        gaps = []

        for match in comparison.function_matches:
            if not (match.c_function and match.fortran_function):
                continue
            c_io = match.c_function.has_io
            f_io = match.fortran_function.has_io

            if c_io and not f_io:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.DIFFERENT_OUTPUT_HANDLING,
                    severity=GapSeverity.LOW,
                    source_language="C",
                    target_language="Fortran",
                    location=f"C:{match.c_function.name}",
                    explanation=(
                        f"C function '{match.c_function.name}' contains I/O operations "
                        f"(printf/scanf) but the Fortran counterpart does not."
                    ),
                    evidence="C: I/O detected; Fortran: no READ/WRITE/PRINT found",
                    confidence=0.75,
                    suggested_resolution=(
                        "Add WRITE(*,*) or READ(*,*) statements to the Fortran implementation "
                        "if I/O is part of the required behavior."
                    ),
                ))
            elif not c_io and f_io:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.DIFFERENT_INPUT_HANDLING,
                    severity=GapSeverity.LOW,
                    source_language="Fortran",
                    target_language="C",
                    location=f"Fortran:{match.fortran_function.name}",
                    explanation=(
                        f"Fortran unit '{match.fortran_function.name}' contains I/O "
                        f"but the C counterpart does not."
                    ),
                    evidence="Fortran: I/O detected; C: no printf/scanf found",
                    confidence=0.75,
                    suggested_resolution=(
                        "Add printf/scanf to the C implementation if I/O is required."
                    ),
                ))

        return gaps

    def _detect_complexity_gaps(self, comparison: ComparisonResult) -> List[GapReport]:
        gaps = []

        for match in comparison.function_matches:
            if not (match.c_function and match.fortran_function):
                continue
            if match.complexity_delta > 3:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.MISSING_BRANCH,
                    severity=GapSeverity.MEDIUM,
                    source_language="C" if match.c_function.cyclomatic_complexity > match.fortran_function.cyclomatic_complexity else "Fortran",
                    target_language="Fortran" if match.c_function.cyclomatic_complexity > match.fortran_function.cyclomatic_complexity else "C",
                    location=(
                        f"C:{match.c_function.name} (CC={match.c_function.cyclomatic_complexity}) "
                        f"vs Fortran:{match.fortran_function.name} (CC={match.fortran_function.cyclomatic_complexity})"
                    ),
                    explanation=(
                        f"Significant complexity difference (Δ={match.complexity_delta}): "
                        f"one implementation may have branches or loops that the other lacks."
                    ),
                    evidence="; ".join(match.notes),
                    confidence=0.7,
                    suggested_resolution=(
                        "Manually review both implementations to check for missing "
                        "IF/ELSE branches or DO loops."
                    ),
                ))

        return gaps

    def _detect_loop_differences(self, comparison: ComparisonResult) -> List[GapReport]:
        gaps = []

        for match in comparison.function_matches:
            if not (match.c_function and match.fortran_function):
                continue
            c_has_loops = match.c_function.has_loops
            f_has_loops = match.fortran_function.has_loops

            if c_has_loops != f_has_loops:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.MISSING_LOOP,
                    severity=GapSeverity.HIGH,
                    source_language="C" if c_has_loops else "Fortran",
                    target_language="Fortran" if c_has_loops else "C",
                    location=(
                        f"C:{match.c_function.name} / "
                        f"Fortran:{match.fortran_function.name}"
                    ),
                    explanation=(
                        "One implementation contains loops while the other does not. "
                        "This likely indicates a significant algorithmic difference."
                    ),
                    evidence=(
                        f"C has_loops={c_has_loops}, "
                        f"Fortran has_loops={f_has_loops}"
                    ),
                    confidence=0.82,
                    suggested_resolution=(
                        "Add equivalent DO loops / for-loops to the implementation "
                        "that is missing them. Verify loop bounds match."
                    ),
                ))

        return gaps

    def _detect_implicit_none(self, comparison: ComparisonResult) -> List[GapReport]:
        """Detect missing IMPLICIT NONE in Fortran (common source of bugs)."""
        gaps = []

        for fn in comparison.fortran_ir.functions:
            if not fn.has_implicit_none:
                gaps.append(GapReport(
                    gap_id=self._next_id(),
                    category=GapCategory.INITIALIZATION_MISMATCH,
                    severity=GapSeverity.LOW,
                    source_language="Fortran",
                    target_language="Fortran",
                    location=f"Fortran:{fn.name}",
                    explanation=(
                        f"Fortran unit '{fn.name}' is missing IMPLICIT NONE. "
                        f"Without it, undeclared variables default to INTEGER (starting with I-N) "
                        f"or REAL, which may cause subtle bugs."
                    ),
                    evidence="IMPLICIT NONE not found in unit header.",
                    confidence=0.95,
                    suggested_resolution=(
                        "Add 'IMPLICIT NONE' immediately after the unit header. "
                        "Then declare all variables explicitly."
                    ),
                ))

        return gaps
