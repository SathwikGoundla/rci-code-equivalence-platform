"""
Fortran Source Code Analyzer

Phase 3: Primary parser is fparser2 (Fortran 2003 full AST).
         Graceful fallback to regex-based structural extraction if AST fails.

Phase 1 regex parser is preserved as fallback and handles unusual code
that fparser2 might reject (e.g. non-standard extensions).
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from app.ir.models import (
    CanonicalType,
    FunctionIR,
    ProgramIR,
    ProgramMetadata,
    VariableIR,
)
from app.analyzers.fortran.fortran_ast_parser import (
    parse_fortran_units   as _ast_parse_units,
    parse_fortran_globals as _ast_parse_globals,
)

logger = logging.getLogger(__name__)

# ── Type Mapping (regex fallback) ─────────────────────────────────────────────
_FORTRAN_TYPE_MAP: dict[str, CanonicalType] = {
    "integer":          CanonicalType.INT32,
    "integer(4)":       CanonicalType.INT32,
    "integer(8)":       CanonicalType.INT64,
    "real":             CanonicalType.FLOAT32,
    "real(4)":          CanonicalType.FLOAT32,
    "real(8)":          CanonicalType.FLOAT64,
    "double precision": CanonicalType.FLOAT64,
    "real(16)":         CanonicalType.FLOAT128,
    "complex":          CanonicalType.COMPLEX64,
    "complex(8)":       CanonicalType.COMPLEX128,
    "logical":          CanonicalType.BOOLEAN,
    "character":        CanonicalType.CHARACTER,
}


def _map_fortran_type(type_str: str) -> CanonicalType:
    key = type_str.strip().lower()
    return _FORTRAN_TYPE_MAP.get(key, CanonicalType.UNKNOWN)


# ── Regex Patterns (fallback) ─────────────────────────────────────────────────
_PROGRAM_PATTERN = re.compile(r'^\s*PROGRAM\s+(\w+)', re.MULTILINE | re.IGNORECASE)
_FUNCTION_PATTERN = re.compile(
    r'^\s*(?:PURE\s+|ELEMENTAL\s+|RECURSIVE\s+)?'
    r'(?:(INTEGER|REAL|DOUBLE\s+PRECISION|COMPLEX|LOGICAL|CHARACTER)\s+)?'
    r'FUNCTION\s+(\w+)\s*\(([^)]*)\)',
    re.MULTILINE | re.IGNORECASE,
)
_SUBROUTINE_PATTERN = re.compile(
    r'^\s*(?:PURE\s+|ELEMENTAL\s+|RECURSIVE\s+)?'
    r'SUBROUTINE\s+(\w+)\s*\(([^)]*)\)',
    re.MULTILINE | re.IGNORECASE,
)
_MODULE_PATTERN   = re.compile(r'^\s*MODULE\s+(\w+)', re.MULTILINE | re.IGNORECASE)
_USE_PATTERN      = re.compile(r'^\s*USE\s+(\w+)',    re.MULTILINE | re.IGNORECASE)
_VAR_DECL_PATTERN = re.compile(
    r'^\s*(INTEGER|REAL|DOUBLE\s+PRECISION|COMPLEX|LOGICAL|CHARACTER)'
    r'(?:\s*\([^)]+\))?'
    r'\s*(?:,\s*INTENT\([^)]+\))?'
    r'\s*(?:::\s*)?'
    r'([\w\s,]+?)(?:\s*=\s*[^!\n]+)?'
    r'\s*(?:!.*)?$',
    re.MULTILINE | re.IGNORECASE,
)
_PARAMETER_PATTERN = re.compile(
    r'(?:,\s*)?PARAMETER\s*(?:::\s*)?\s*(\w+)\s*=\s*([^,\n!]+)',
    re.MULTILINE | re.IGNORECASE,
)
_IMPLICIT_NONE_PATTERN = re.compile(r'^\s*IMPLICIT\s+NONE', re.MULTILINE | re.IGNORECASE)
_DO_PATTERN    = re.compile(r'^\s*DO\s+',    re.MULTILINE | re.IGNORECASE)
_IF_PATTERN    = re.compile(r'^\s*IF\s*\(',  re.MULTILINE | re.IGNORECASE)
_CALL_PATTERN  = re.compile(r'^\s*CALL\s+(\w+)', re.MULTILINE | re.IGNORECASE)
_IO_PATTERN    = re.compile(r'^\s*(READ|WRITE|PRINT)\s*[\(*]', re.MULTILINE | re.IGNORECASE)


def _find_unit_end(source: str, start_pos: int, unit_keyword: str) -> int:
    end_pattern = re.compile(
        rf'^\s*END\s*(?:{unit_keyword})?(?:\s+\w+)?\s*(?:!.*)?$',
        re.MULTILINE | re.IGNORECASE,
    )
    match = end_pattern.search(source, start_pos)
    return match.end() if match else len(source)


def _count_loc(source: str) -> int:
    count = 0
    for line in source.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("!"):
            count += 1
    return count


def _estimate_complexity(body: str) -> int:
    decisions = re.findall(
        r'\b(IF\s*\(|ELSE\s+IF|DO\s+|CASE\s*\(|\.AND\.|\.OR\.)\b',
        body, re.IGNORECASE,
    )
    return 1 + len(decisions)


def _parse_fortran_vars(decl_str: str, type_str: str) -> List[VariableIR]:
    vars_out: List[VariableIR] = []
    names_str = re.sub(r'\(.*?\)', '', decl_str)
    for name in names_str.split(","):
        name = name.strip()
        if name and re.match(r'^\w+$', name):
            vars_out.append(VariableIR(
                name=name,
                canonical_type=_map_fortran_type(type_str),
                original_type_str=type_str,
                is_parameter=False,
            ))
    return vars_out


def _parse_program_units(source: str) -> List[FunctionIR]:
    """Regex-based program unit extraction (Phase 1 fallback)."""
    units: List[FunctionIR] = []

    for match in _PROGRAM_PATTERN.finditer(source):
        prog_name = match.group(1)
        body_start = match.end()
        body_end = _find_unit_end(source, body_start, "PROGRAM")
        body = source[body_start:body_end]
        units.append(FunctionIR(
            name=prog_name,
            source_language="Fortran",
            kind="program",
            parameters=[],
            return_type=None,
            calls=_CALL_PATTERN.findall(body),
            source_line_start=source[:match.start()].count("\n") + 1,
            source_line_end=source[:body_end].count("\n") + 1,
            loc=_count_loc(body),
            cyclomatic_complexity=_estimate_complexity(body),
            has_implicit_none=bool(_IMPLICIT_NONE_PATTERN.search(body)),
            has_io=bool(_IO_PATTERN.search(body)),
            has_loops=bool(_DO_PATTERN.search(body)),
            has_conditionals=bool(_IF_PATTERN.search(body)),
        ))

    for match in _FUNCTION_PATTERN.finditer(source):
        ret_type_str = (match.group(1) or "").strip()
        func_name    = match.group(2).strip()
        params_str   = match.group(3).strip()
        body_start   = match.end()
        body_end     = _find_unit_end(source, body_start, "FUNCTION")
        body         = source[body_start:body_end]
        params = [
            VariableIR(name=p.strip(), canonical_type=CanonicalType.UNKNOWN)
            for p in params_str.split(",") if p.strip()
        ]
        units.append(FunctionIR(
            name=func_name,
            source_language="Fortran",
            kind="function",
            parameters=params,
            return_type=_map_fortran_type(ret_type_str) if ret_type_str else None,
            calls=_CALL_PATTERN.findall(body),
            source_line_start=source[:match.start()].count("\n") + 1,
            source_line_end=source[:body_end].count("\n") + 1,
            loc=_count_loc(body),
            cyclomatic_complexity=_estimate_complexity(body),
            has_implicit_none=bool(_IMPLICIT_NONE_PATTERN.search(body)),
            has_io=bool(_IO_PATTERN.search(body)),
            has_loops=bool(_DO_PATTERN.search(body)),
            has_conditionals=bool(_IF_PATTERN.search(body)),
        ))

    for match in _SUBROUTINE_PATTERN.finditer(source):
        sub_name   = match.group(1).strip()
        params_str = match.group(2).strip()
        body_start = match.end()
        body_end   = _find_unit_end(source, body_start, "SUBROUTINE")
        body       = source[body_start:body_end]
        params = [
            VariableIR(name=p.strip(), canonical_type=CanonicalType.UNKNOWN)
            for p in params_str.split(",") if p.strip()
        ]
        units.append(FunctionIR(
            name=sub_name,
            source_language="Fortran",
            kind="subroutine",
            parameters=params,
            return_type=None,
            calls=_CALL_PATTERN.findall(body),
            source_line_start=source[:match.start()].count("\n") + 1,
            source_line_end=source[:body_end].count("\n") + 1,
            loc=_count_loc(body),
            cyclomatic_complexity=_estimate_complexity(body),
            has_implicit_none=bool(_IMPLICIT_NONE_PATTERN.search(body)),
            has_io=bool(_IO_PATTERN.search(body)),
            has_loops=bool(_DO_PATTERN.search(body)),
            has_conditionals=bool(_IF_PATTERN.search(body)),
        ))

    return units


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_fortran_source(source: str, filename: str = "<unknown>") -> ProgramIR:
    """
    Analyze Fortran source code and produce a ProgramIR.

    Phase 3: Uses fparser2 (Fortran 2003 AST) as primary parser.
             Falls back to Phase 1 regex parser if AST fails.

    NOTE: Array index normalization (1-based → 0-based logical) is deferred
    to the IR comparison layer to preserve original evidence for gap reports.
    """
    warnings: List[str] = []
    total_lines = len(source.splitlines())
    total_loc = _count_loc(source)

    # ── Try fparser2 AST first ────────────────────────────────────────────────
    parser_used = "fparser2"
    functions   = _ast_parse_units(source, filename)
    global_vars, constants, uses, modules = _ast_parse_globals(source, filename)

    if not functions and source.strip():
        logger.info("fparser2 returned no units for %s; trying regex fallback", filename)
        warnings.append("fparser2 AST parser returned no units; regex fallback used.")
        parser_used = "regex-structural (fallback)"
        functions   = _parse_program_units(source)
        uses        = _USE_PATTERN.findall(source)
        modules     = _MODULE_PATTERN.findall(source)
        constants   = []
        for match in _PARAMETER_PATTERN.finditer(source):
            name, value = match.group(1).strip(), match.group(2).strip()
            constants.append(VariableIR(
                name=name,
                canonical_type=CanonicalType.UNKNOWN,
                is_parameter=True,
                initial_value=value,
                original_type_str="PARAMETER",
            ))
        global_vars = []
        for match in _VAR_DECL_PATTERN.finditer(source):
            type_str  = match.group(1).strip()
            names_str = match.group(2).strip()
            global_vars.extend(_parse_fortran_vars(names_str, type_str))

    if not functions:
        warnings.append(
            "No PROGRAM/FUNCTION/SUBROUTINE detected. "
            "Verify the file is valid Fortran 90+ free-form source."
        )

    return ProgramIR(
        metadata=ProgramMetadata(
            filename=filename,
            source_language="Fortran",
            language_standard="F2003",
            total_lines=total_lines,
            total_loc=total_loc,
            parse_warnings=warnings,
            parser_used=parser_used,
        ),
        functions=functions,
        global_variables=global_vars,
        constants=constants,
        includes=uses,
        modules=modules,
    )
