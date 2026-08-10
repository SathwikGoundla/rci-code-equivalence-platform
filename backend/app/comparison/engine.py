"""
IR Comparison Engine

Compares two ProgramIR objects (one C, one Fortran) and identifies structural
and semantic differences. This engine feeds data to the Gap Detection Engine.

Phase 1: Function-level structural comparison.
Phase 5+: Will add deep semantic comparison, control-flow graph diff, data-flow analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.ir.models import CanonicalType, FunctionIR, ProgramIR

logger = logging.getLogger(__name__)


@dataclass
class FunctionMatchResult:
    """Result of matching a C function to a Fortran counterpart."""
    c_function: Optional[FunctionIR]
    fortran_function: Optional[FunctionIR]
    match_type: str  # "exact" | "fuzzy" | "c_only" | "fortran_only"
    name_similarity: float  # 0.0 - 1.0
    param_count_match: bool
    return_type_match: bool
    complexity_delta: int
    notes: List[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """Full comparison result between C and Fortran ProgramIRs."""
    c_ir: ProgramIR
    fortran_ir: ProgramIR
    function_matches: List[FunctionMatchResult] = field(default_factory=list)
    c_only_functions: List[str] = field(default_factory=list)
    fortran_only_functions: List[str] = field(default_factory=list)
    matched_functions: List[Tuple[str, str]] = field(default_factory=list)
    type_mismatches: List[Dict] = field(default_factory=list)
    structural_score: float = 0.0  # 0.0 = completely different, 1.0 = identical structure
    notes: List[str] = field(default_factory=list)


def _name_similarity(a: str, b: str) -> float:
    """
    Simple name similarity: normalized edit distance.
    In Phase 5 this will use semantic function name embeddings.
    """
    a, b = a.lower(), b.lower()
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.8

    # Levenshtein distance (simple iterative)
    if len(a) == 0 or len(b) == 0:
        return 0.0
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    distance = dp[n]
    return 1.0 - (distance / max(m, n))


def _match_functions(
    c_fns: List[FunctionIR],
    f_fns: List[FunctionIR],
) -> List[FunctionMatchResult]:
    """
    Match C functions to Fortran functions by name similarity.
    Returns a list of FunctionMatchResult.
    """
    results: List[FunctionMatchResult] = []
    used_fortran: Set[str] = set()

    for c_fn in c_fns:
        best_match: Optional[FunctionIR] = None
        best_score = 0.0

        for f_fn in f_fns:
            if f_fn.name in used_fortran:
                continue
            score = _name_similarity(c_fn.name, f_fn.name)
            if score > best_score:
                best_score = score
                best_match = f_fn

        if best_match and best_score >= 0.6:
            used_fortran.add(best_match.name)
            notes = []

            param_match = len(c_fn.parameters) == len(best_match.parameters)
            if not param_match:
                notes.append(
                    f"Parameter count: C={len(c_fn.parameters)}, "
                    f"Fortran={len(best_match.parameters)}"
                )

            # Return type comparison
            ret_match = True
            if c_fn.return_type and best_match.return_type:
                ret_match = c_fn.return_type == best_match.return_type
                if not ret_match:
                    notes.append(
                        f"Return type: C={c_fn.return_type.value}, "
                        f"Fortran={best_match.return_type.value}"
                    )

            complexity_delta = abs(
                c_fn.cyclomatic_complexity - best_match.cyclomatic_complexity
            )
            if complexity_delta > 2:
                notes.append(
                    f"Complexity delta={complexity_delta} "
                    f"(C={c_fn.cyclomatic_complexity}, "
                    f"Fortran={best_match.cyclomatic_complexity})"
                )

            results.append(
                FunctionMatchResult(
                    c_function=c_fn,
                    fortran_function=best_match,
                    match_type="exact" if best_score == 1.0 else "fuzzy",
                    name_similarity=best_score,
                    param_count_match=param_match,
                    return_type_match=ret_match,
                    complexity_delta=complexity_delta,
                    notes=notes,
                )
            )
        else:
            # C function has no Fortran counterpart
            results.append(
                FunctionMatchResult(
                    c_function=c_fn,
                    fortran_function=None,
                    match_type="c_only",
                    name_similarity=0.0,
                    param_count_match=False,
                    return_type_match=False,
                    complexity_delta=0,
                    notes=[f"No Fortran counterpart found for C function '{c_fn.name}'"],
                )
            )

    # Fortran functions with no C counterpart
    matched_fortran_names = {
        r.fortran_function.name
        for r in results
        if r.fortran_function
    }
    for f_fn in f_fns:
        if f_fn.name not in matched_fortran_names:
            results.append(
                FunctionMatchResult(
                    c_function=None,
                    fortran_function=f_fn,
                    match_type="fortran_only",
                    name_similarity=0.0,
                    param_count_match=False,
                    return_type_match=False,
                    complexity_delta=0,
                    notes=[f"No C counterpart found for Fortran unit '{f_fn.name}'"],
                )
            )

    return results


def compare_programs(c_ir: ProgramIR, fortran_ir: ProgramIR) -> ComparisonResult:
    """
    Compare C and Fortran ProgramIRs and return a ComparisonResult.
    """
    logger.info(
        "Comparing C IR (%d functions) with Fortran IR (%d functions)",
        len(c_ir.functions),
        len(fortran_ir.functions),
    )

    function_matches = _match_functions(c_ir.functions, fortran_ir.functions)

    c_only = [
        m.c_function.name for m in function_matches
        if m.match_type == "c_only" and m.c_function
    ]
    fortran_only = [
        m.fortran_function.name for m in function_matches
        if m.match_type == "fortran_only" and m.fortran_function
    ]
    matched = [
        (m.c_function.name, m.fortran_function.name)
        for m in function_matches
        if m.c_function and m.fortran_function
    ]

    # Structural score: fraction of functions that have counterparts, weighted by name similarity
    total = len(c_ir.functions) + len(fortran_ir.functions)
    if total == 0:
        structural_score = 1.0
    else:
        matched_weight = sum(
            m.name_similarity
            for m in function_matches
            if m.c_function and m.fortran_function
        )
        structural_score = (2 * matched_weight) / total

    notes = []
    if not c_ir.functions:
        notes.append("WARNING: No functions detected in C source.")
    if not fortran_ir.functions:
        notes.append("WARNING: No program units detected in Fortran source.")

    return ComparisonResult(
        c_ir=c_ir,
        fortran_ir=fortran_ir,
        function_matches=function_matches,
        c_only_functions=c_only,
        fortran_only_functions=fortran_only,
        matched_functions=matched,
        structural_score=round(structural_score, 3),
        notes=notes,
    )
