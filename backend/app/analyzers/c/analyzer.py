"""
C Source Code Analyzer

Phase 3: Primary parser is tree-sitter (full AST).
         Graceful fallback to regex-based structural extraction if AST fails.

Phase 1 regex parser is preserved as fallback and handles unusual or
syntactically ambiguous C that tree-sitter might reject.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from app.ir.models import (
    CanonicalType,
    FunctionIR,
    ProgramIR,
    ProgramMetadata,
    VariableIR,
)
from app.analyzers.c.c_ast_parser import (
    parse_c_functions as _ast_parse_functions,
    parse_c_globals   as _ast_parse_globals,
)

logger = logging.getLogger(__name__)

# ── Type Mapping (regex fallback) ─────────────────────────────────────────────
_C_TYPE_MAP: dict[str, CanonicalType] = {
    "char":         CanonicalType.INT8,
    "short":        CanonicalType.INT16,
    "int":          CanonicalType.INT32,
    "long":         CanonicalType.INT64,
    "float":        CanonicalType.FLOAT32,
    "double":       CanonicalType.FLOAT64,
    "long double":  CanonicalType.FLOAT128,
    "void":         CanonicalType.VOID,
    "_Bool":        CanonicalType.BOOLEAN,
    "bool":         CanonicalType.BOOLEAN,
}

# ── Regex Patterns (fallback) ─────────────────────────────────────────────────
_FUNC_PATTERN = re.compile(
    r"""
    ^                                       # start of line
    (?:static\s+|extern\s+|inline\s+)*     # optional qualifiers
    (?:const\s+)?                           # optional const
    ((?:long\s+double|long\s+long|long\s+int|unsigned\s+\w+|signed\s+\w+|\w+)\s*\*?) # return type
    \s+
    (\w+)                                   # function name
    \s*\(                                   # open paren
    ([^)]*?)                               # params (non-greedy)
    \)                                      # close paren
    \s*\{                                   # open brace
    """,
    re.MULTILINE | re.VERBOSE,
)

_INCLUDE_PATTERN = re.compile(r'^\s*#include\s*[<"]([^>"]+)[>"]', re.MULTILINE)
_DEFINE_PATTERN  = re.compile(r'^\s*#define\s+(\w+)\s+(.+)', re.MULTILINE)
_VAR_PATTERN     = re.compile(
    r'^\s*(int|float|double|long|char|short|bool|_Bool|long\s+double)\s+'
    r'(\w+)(?:\s*=\s*([^;]+))?;',
    re.MULTILINE,
)


def _map_c_type(type_str: str) -> CanonicalType:
    clean = type_str.strip().rstrip("*").strip()
    return _C_TYPE_MAP.get(clean, CanonicalType.UNKNOWN)


def _count_loc(source: str) -> int:
    lines = source.splitlines()
    count = 0
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        if "/*" in stripped:
            in_block_comment = True
        if "*/" in stripped:
            in_block_comment = False
            continue
        if in_block_comment:
            continue
        if stripped and not stripped.startswith("//"):
            count += 1
    return count


def _estimate_complexity(func_body: str) -> int:
    decision_keywords = re.findall(
        r'\b(if|else\s+if|for|while|do|case|&&|\|\|)\b', func_body
    )
    return 1 + len(decision_keywords)


def _parse_functions(source: str) -> List[FunctionIR]:
    """Regex-based function extraction (Phase 1 fallback)."""
    functions: List[FunctionIR] = []

    lines = source.splitlines()
    line_starts: dict[int, int] = {}
    pos = 0
    for i, line in enumerate(lines):
        line_starts[pos] = i + 1
        pos += len(line) + 1

    for match in _FUNC_PATTERN.finditer(source):
        return_type_str = match.group(1).strip()
        func_name = match.group(2).strip()
        params_str = match.group(3).strip()

        if func_name in {"if", "while", "for", "switch", "return"}:
            continue

        match_pos = match.start()
        source_line = 1
        for p, ln in sorted(line_starts.items()):
            if p <= match_pos:
                source_line = ln

        params: List[VariableIR] = []
        if params_str and params_str.lower() not in {"void", ""}:
            for param in params_str.split(","):
                param = param.strip()
                parts = param.rsplit(None, 1)
                if len(parts) == 2:
                    ptype_str, pname = parts
                    pname = pname.lstrip("*").strip()
                    params.append(VariableIR(
                        name=pname,
                        canonical_type=_map_c_type(ptype_str),
                        original_type_str=ptype_str,
                    ))

        start_brace = source.find("{", match.end() - 1)
        body_end = start_brace
        depth = 0
        for i, ch in enumerate(source[start_brace:], start=start_brace):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body_end = i
                    break

        func_body = source[start_brace:body_end + 1] if start_brace < body_end else ""
        loc = _count_loc(func_body)
        complexity = _estimate_complexity(func_body)

        call_matches = re.findall(r'\b(\w+)\s*\(', func_body)
        calls = list(set(c for c in call_matches if c != func_name and c not in {
            "if", "for", "while", "switch", "sizeof", "return"
        }))

        functions.append(FunctionIR(
            name=func_name,
            source_language="C",
            kind="function",
            parameters=params,
            return_type=_map_c_type(return_type_str),
            calls=calls,
            source_line_start=source_line,
            loc=loc,
            cyclomatic_complexity=complexity,
            has_io=bool(re.search(r'\b(printf|scanf|fprintf|fread|fwrite)\b', func_body)),
            has_loops=bool(re.search(r'\b(for|while|do)\s*\(', func_body)),
            has_conditionals=bool(re.search(r'\b(if|switch)\s*\(', func_body)),
        ))

    return functions


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_c_source(source: str, filename: str = "<unknown>") -> ProgramIR:
    """
    Analyze C source code and produce a ProgramIR.

    Phase 3: Uses tree-sitter for full AST extraction.
             Falls back to Phase 1 regex parser if AST fails.

    NOTE: Array index normalization (0-based) is deferred to the IR
    comparison layer to preserve original evidence for gap reports.
    """
    warnings: List[str] = []
    total_lines = len(source.splitlines())
    total_loc = _count_loc(source)

    # ── Try AST parser first ──────────────────────────────────────────────────
    parser_used = "tree-sitter"
    functions   = _ast_parse_functions(source, filename)
    global_vars, constants, includes = _ast_parse_globals(source, filename)

    if not functions and source.strip():
        # AST returned nothing on non-empty source — try regex fallback
        logger.info("tree-sitter returned no functions for %s; trying regex fallback", filename)
        warnings.append("tree-sitter AST parser returned no functions; regex fallback used.")
        parser_used  = "regex-structural (fallback)"
        functions    = _parse_functions(source)
        includes     = _INCLUDE_PATTERN.findall(source)
        constants    = []
        for name, value in _DEFINE_PATTERN.findall(source):
            constants.append(VariableIR(
                name=name,
                canonical_type=CanonicalType.UNKNOWN,
                is_parameter=True,
                initial_value=value.strip(),
                original_type_str="#define",
            ))
        global_vars = []
        for match in _VAR_PATTERN.finditer(source):
            type_str, var_name, init_val = match.groups()
            prefix = source[:match.start()]
            if prefix.count("{") == prefix.count("}"):
                global_vars.append(VariableIR(
                    name=var_name,
                    canonical_type=_map_c_type(type_str),
                    initial_value=init_val.strip() if init_val else None,
                    original_type_str=type_str,
                ))

    if not functions:
        warnings.append(
            "No functions detected. Check that the uploaded file contains "
            "valid C function definitions."
        )

    return ProgramIR(
        metadata=ProgramMetadata(
            filename=filename,
            source_language="C",
            language_standard="C99",
            total_lines=total_lines,
            total_loc=total_loc,
            parse_warnings=warnings,
            parser_used=parser_used,
        ),
        functions=functions,
        global_variables=global_vars,
        constants=constants,
        includes=includes,
    )
