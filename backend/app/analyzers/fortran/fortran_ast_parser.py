"""
fparser2 Fortran AST Parser  (Phase 3)

Replaces the regex-based Fortran structural extractor with a full AST walk
using fparser 0.1.4 (fparser.two — Fortran 2003 standard).

Public surface
--------------
    parse_fortran_units(source: str, filename: str) -> List[FunctionIR]
    parse_fortran_globals(source: str, filename: str)
        -> Tuple[List[VariableIR], List[VariableIR], List[str], List[str]]

Both functions are SAFE: they never raise; on any error they return
empty collections so the caller can fall back to the regex parser.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from app.ir.models import (
    CanonicalType,
    FunctionIR,
    VariableIR,
)

logger = logging.getLogger(__name__)

# ── Lazy-import fparser2 (heavy import; only paid once) ───────────────────────
try:
    from fparser.two.parser import ParserFactory
    from fparser.two import Fortran2003 as F2003
    from fparser.common.readfortran import FortranStringReader
    _fparser2_available = True
    _PARSER_FACTORY = ParserFactory().create(std="f2003")
except Exception as _fparser_import_err:
    _fparser2_available = False
    _PARSER_FACTORY = None  # type: ignore
    logger.warning("fparser2 not available: %s", _fparser_import_err)


# ── Type mapping ──────────────────────────────────────────────────────────────
_FORTRAN_TYPE_MAP: dict[str, CanonicalType] = {
    "integer":           CanonicalType.INT32,
    "integer(4)":        CanonicalType.INT32,
    "integer(kind=4)":   CanonicalType.INT32,
    "integer(8)":        CanonicalType.INT64,
    "integer(kind=8)":   CanonicalType.INT64,
    "real":              CanonicalType.FLOAT32,
    "real(4)":           CanonicalType.FLOAT32,
    "real(kind=4)":      CanonicalType.FLOAT32,
    "real(8)":           CanonicalType.FLOAT64,
    "real(kind=8)":      CanonicalType.FLOAT64,
    "double precision":  CanonicalType.FLOAT64,
    "real(16)":          CanonicalType.FLOAT128,
    "complex":           CanonicalType.COMPLEX64,
    "complex(8)":        CanonicalType.COMPLEX128,
    "logical":           CanonicalType.BOOLEAN,
    "character":         CanonicalType.CHARACTER,
}


def _map_fortran_type(type_str: str) -> CanonicalType:
    key = type_str.strip().lower()
    return _FORTRAN_TYPE_MAP.get(key, CanonicalType.UNKNOWN)


# ── fparser2 node helpers ─────────────────────────────────────────────────────

def _find_nodes(root, *classes):
    """Recursively collect all nodes of the given fparser2 class(es)."""
    results = []
    _walk(root, classes, results)
    return results


def _walk(node, classes, out):
    if isinstance(node, classes):
        out.append(node)
    children = getattr(node, "children", None)
    if children:
        for child in children:
            if child is not None:
                _walk(child, classes, out)


def _node_str(node) -> str:
    try:
        return node.tostr().strip()
    except Exception:
        return str(node).strip()


def _count_loc(source: str) -> int:
    count = 0
    for line in source.splitlines():
        s = line.strip()
        if s and not s.startswith("!"):
            count += 1
    return count


def _estimate_complexity(source: str) -> int:
    decisions = re.findall(
        r'\b(IF\s*\(|ELSE\s+IF|DO\s+|CASE\s*\(|\.AND\.|\.OR\.)\b',
        source, re.IGNORECASE,
    )
    return 1 + len(decisions)


# ── Intent extraction ─────────────────────────────────────────────────────────

def _parse_intent(attr_spec_str: str) -> Tuple[bool, bool]:
    """Return (is_intent_in, is_intent_out) from an attribute spec string."""
    s = attr_spec_str.upper()
    if "INTENT(IN)" in s and "OUT" not in s:
        return True, False
    if "INTENT(OUT)" in s:
        return False, True
    if "INTENT(INOUT)" in s:
        return True, True
    return False, False


# ── Type declaration parsing ──────────────────────────────────────────────────

def _parse_type_decl(decl_node) -> List[VariableIR]:
    """
    Parse a Type_Declaration_Stmt into VariableIR entries.
    Structure: Type_Spec :: Attr_Spec_List :: Entity_Decl_List
    """
    out: List[VariableIR] = []
    try:
        decl_str = _node_str(decl_node)
        # Extract type spec (first element of children)
        children = list(decl_node.children) if hasattr(decl_node, "children") else []
        type_spec_node = children[0] if children else None
        type_str = _node_str(type_spec_node) if type_spec_node else ""

        # Intent from attributes
        is_in, is_out = False, False
        is_param = False
        for child in children[1:]:
            child_s = _node_str(child).upper()
            if "INTENT" in child_s:
                is_in, is_out = _parse_intent(child_s)
            if "PARAMETER" in child_s:
                is_param = True

        canonical = _map_fortran_type(type_str.lower())

        # Entity declarations (variable names + optional initializers)
        # The entity_decl_list is usually the last child
        entity_list = children[-1] if len(children) > 1 else None
        if entity_list is None:
            return out

        entity_str = _node_str(entity_list)
        # Split on commas not inside parens
        names = _split_entities(entity_str)
        for entity in names:
            entity = entity.strip()
            # Handle array dimensions: name(dim) or name(dim1, dim2)
            is_array = False
            name = entity
            if "(" in entity:
                is_array = True
                name = entity[:entity.index("(")].strip()
            # Handle initializer: name = value
            init_val = None
            if "=" in name:
                parts = name.split("=", 1)
                name = parts[0].strip()
                init_val = parts[1].strip()

            name = name.strip()
            if name and re.match(r"^[A-Za-z_]\w*$", name):
                out.append(VariableIR(
                    name=name,
                    canonical_type=canonical,
                    original_type_str=type_str,
                    is_array=is_array,
                    is_parameter=is_param,
                    is_intent_in=is_in,
                    is_intent_out=is_out,
                    initial_value=init_val,
                ))
    except Exception as exc:
        logger.debug("type_decl parse error: %s", exc)
    return out


def _split_entities(s: str) -> List[str]:
    """Split comma-separated entity list respecting parentheses."""
    parts, depth, current = [], 0, []
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


# ── Unit body analysis ────────────────────────────────────────────────────────

def _analyse_body(body_str: str) -> Tuple[bool, bool, bool, bool, List[str]]:
    """
    Returns (has_loops, has_conditionals, has_io, has_implicit_none, calls).
    """
    has_loops        = bool(re.search(r'^\s*DO\b', body_str, re.MULTILINE | re.IGNORECASE))
    has_cond         = bool(re.search(r'^\s*IF\s*\(', body_str, re.MULTILINE | re.IGNORECASE))
    has_io           = bool(re.search(r'^\s*(READ|WRITE|PRINT)\s*[\(*]',
                                      body_str, re.MULTILINE | re.IGNORECASE))
    has_implicit_none = bool(re.search(r'^\s*IMPLICIT\s+NONE', body_str,
                                        re.MULTILINE | re.IGNORECASE))
    call_matches = re.findall(r'^\s*CALL\s+(\w+)', body_str, re.MULTILINE | re.IGNORECASE)
    return has_loops, has_cond, has_io, has_implicit_none, call_matches


# ── Subprogram extraction ─────────────────────────────────────────────────────

def _extract_subprogram(node, source_lines: List[str]) -> Optional[FunctionIR]:
    """
    Convert a Subroutine_Subprogram or Function_Subprogram fparser2 node
    into a FunctionIR.
    """
    try:
        if not hasattr(node, "children") or not node.children:
            return None

        stmt = node.children[0]  # Subroutine_Stmt or Function_Stmt
        body_str = _node_str(node)

        # ── Name ──
        name = ""
        try:
            name_node = stmt.items[1] if hasattr(stmt, "items") else None
            name = _node_str(name_node) if name_node else _node_str(stmt).split("(")[0].split()[-1]
        except Exception:
            name = re.search(r'\b(\w+)\s*\(', _node_str(stmt) or "")
            name = name.group(1) if name else "unknown"

        # ── Kind ──
        is_function   = "Function" in type(node).__name__
        is_subroutine = "Subroutine" in type(node).__name__
        kind = "function" if is_function else "subroutine"

        # ── Parameters (dummy argument list) ──
        params: List[VariableIR] = []
        try:
            # dummy_arg_list is items[2] for subroutine_stmt
            dummy_list = stmt.items[2] if hasattr(stmt, "items") and len(stmt.items) > 2 else None
            if dummy_list:
                dummy_str = _node_str(dummy_list)
                for pname in dummy_str.split(","):
                    pname = pname.strip()
                    if pname and re.match(r'^[A-Za-z_]\w*$', pname):
                        params.append(VariableIR(
                            name=pname,
                            canonical_type=CanonicalType.UNKNOWN,
                        ))
        except Exception:
            pass

        # ── Return type (functions only) ──
        return_type: Optional[CanonicalType] = None
        if is_function:
            try:
                prefix = stmt.items[0]  # Prefix or None
                if prefix:
                    return_type = _map_fortran_type(_node_str(prefix).lower())
            except Exception:
                pass

        # ── Body declarations → typed parameters + locals ──
        local_vars: List[VariableIR] = []
        try:
            type_decls = _find_nodes(node, F2003.Type_Declaration_Stmt)
            declared: List[VariableIR] = []
            for td in type_decls:
                declared.extend(_parse_type_decl(td))

            # Match declared names against dummy parameter list
            param_names = {p.name.lower() for p in params}
            for var in declared:
                if var.name.lower() in param_names:
                    # Update the param entry with real type + intent
                    for p in params:
                        if p.name.lower() == var.name.lower():
                            p.canonical_type  = var.canonical_type
                            p.original_type_str = var.original_type_str
                            p.is_intent_in    = var.is_intent_in
                            p.is_intent_out   = var.is_intent_out
                            p.is_array        = var.is_array
                else:
                    local_vars.append(var)
        except Exception as exc:
            logger.debug("Declaration parse error for %s: %s", name, exc)

        # ── Body analysis ──
        has_loops, has_cond, has_io, has_implicit_none, calls = _analyse_body(body_str)

        # ── LOC + complexity ──
        loc = _count_loc(body_str)
        complexity = _estimate_complexity(body_str)

        # ── Source lines ──
        # fparser2 nodes don't always carry line info; best effort
        src_line_start: Optional[int] = None
        src_line_end:   Optional[int] = None
        try:
            src_line_start = getattr(node, "item", None) and node.item.span[0]
        except Exception:
            pass

        return FunctionIR(
            name=name,
            source_language="Fortran",
            kind=kind,
            parameters=params,
            local_variables=local_vars,
            return_type=return_type,
            calls=calls,
            source_line_start=src_line_start,
            source_line_end=src_line_end,
            loc=loc,
            cyclomatic_complexity=complexity,
            has_implicit_none=has_implicit_none,
            has_io=has_io,
            has_loops=has_loops,
            has_conditionals=has_cond,
        )

    except Exception as exc:
        logger.debug("_extract_subprogram error: %s", exc)
        return None


def _extract_main_program(node) -> Optional[FunctionIR]:
    """Handle PROGRAM ... END PROGRAM."""
    try:
        body_str = _node_str(node)
        # Program name
        prog_stmt = node.children[0] if node.children else None
        name = "main"
        if prog_stmt:
            m = re.search(r'PROGRAM\s+(\w+)', _node_str(prog_stmt), re.IGNORECASE)
            if m:
                name = m.group(1)

        has_loops, has_cond, has_io, has_implicit_none, calls = _analyse_body(body_str)
        loc = _count_loc(body_str)
        complexity = _estimate_complexity(body_str)

        # Local variables
        local_vars: List[VariableIR] = []
        try:
            type_decls = _find_nodes(node, F2003.Type_Declaration_Stmt)
            for td in type_decls:
                local_vars.extend(_parse_type_decl(td))
        except Exception:
            pass

        return FunctionIR(
            name=name,
            source_language="Fortran",
            kind="program",
            parameters=[],
            local_variables=local_vars,
            return_type=None,
            calls=calls,
            loc=loc,
            cyclomatic_complexity=complexity,
            has_implicit_none=has_implicit_none,
            has_io=has_io,
            has_loops=has_loops,
            has_conditionals=has_cond,
        )
    except Exception as exc:
        logger.debug("_extract_main_program error: %s", exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def parse_fortran_units(source: str, filename: str = "<unknown>") -> List[FunctionIR]:
    """
    Parse Fortran source with fparser2 and return a list of FunctionIR.
    Returns [] on any error (caller should fall back to regex parser).
    """
    if not _fparser2_available:
        logger.warning("fparser2 not available; skipping AST parse for %s", filename)
        return []
    try:
        reader = FortranStringReader(source, ignore_comments=False)
        ast = _PARSER_FACTORY(reader)

        if ast is None:
            return []

        units: List[FunctionIR] = []

        # Main program
        for node in _find_nodes(ast, F2003.Main_Program):
            ir = _extract_main_program(node)
            if ir:
                units.append(ir)

        # Subroutines + Functions
        for node in _find_nodes(ast, F2003.Subroutine_Subprogram,
                                       F2003.Function_Subprogram):
            ir = _extract_subprogram(node, source.splitlines())
            if ir:
                units.append(ir)

        return units

    except Exception as exc:
        logger.warning("fparser2 parse failed for %s: %s", filename, exc)
        return []


def parse_fortran_globals(
    source: str,
    filename: str = "<unknown>",
) -> Tuple[List[VariableIR], List[VariableIR], List[str], List[str]]:
    """
    Extract module-level variables, PARAMETER constants, USE modules, MODULE names.
    Returns (global_vars, constants, uses, modules).
    """
    if not _fparser2_available:
        return [], [], [], []
    try:
        reader = FortranStringReader(source, ignore_comments=False)
        ast = _PARSER_FACTORY(reader)
        if ast is None:
            return [], [], [], []

        global_vars: List[VariableIR] = []
        constants:   List[VariableIR] = []
        uses:        List[str] = []
        modules:     List[str] = []

        # USE statements
        for node in _find_nodes(ast, F2003.Use_Stmt):
            s = _node_str(node)
            m = re.search(r'USE\s+(\w+)', s, re.IGNORECASE)
            if m:
                uses.append(m.group(1))

        # MODULE names
        for node in _find_nodes(ast, F2003.Module):
            stmt = node.children[0] if node.children else None
            if stmt:
                m = re.search(r'MODULE\s+(\w+)', _node_str(stmt), re.IGNORECASE)
                if m:
                    modules.append(m.group(1))

        # Module-level type declarations (outside subprograms)
        # Walk only top-level children of Program / Module
        for child in (ast.children if hasattr(ast, "children") else []):
            if child is None:
                continue
            if isinstance(child, (F2003.Subroutine_Subprogram,
                                   F2003.Function_Subprogram,
                                   F2003.Main_Program)):
                continue
            if isinstance(child, F2003.Type_Declaration_Stmt):
                entries = _parse_type_decl(child)
                for e in entries:
                    if e.is_parameter:
                        constants.append(e)
                    else:
                        global_vars.append(e)

        return global_vars, constants, uses, modules

    except Exception as exc:
        logger.warning("fparser2 global parse failed for %s: %s", filename, exc)
        return [], [], [], []
