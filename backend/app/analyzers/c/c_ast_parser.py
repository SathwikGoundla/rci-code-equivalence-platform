"""
tree-sitter C AST Parser  (Phase 3)

Replaces the regex-based C structural extractor with a full AST walk
using tree-sitter 0.22.x + tree-sitter-c 0.21.x.

Public surface
--------------
    parse_c_functions(source: str, filename: str) -> List[FunctionIR]
    parse_c_globals(source: str) -> Tuple[List[VariableIR], List[VariableIR], List[str]]

Both functions are SAFE: they never raise; on any error they return
empty collections so the caller can fall back to the regex parser.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

import tree_sitter_c as tsc
from tree_sitter import Language, Node, Parser

from app.ir.models import (
    CanonicalType,
    FunctionIR,
    VariableIR,
)

logger = logging.getLogger(__name__)

# ── Singleton language + parser (thread-safe after module load) ───────────────
_C_LANGUAGE = Language(tsc.language())
_PARSER = Parser(_C_LANGUAGE)

# ── Type mapping ──────────────────────────────────────────────────────────────
_C_TYPE_MAP: dict[str, CanonicalType] = {
    "char":         CanonicalType.INT8,
    "short":        CanonicalType.INT16,
    "int":          CanonicalType.INT32,
    "long":         CanonicalType.INT64,
    "long long":    CanonicalType.INT64,
    "float":        CanonicalType.FLOAT32,
    "double":       CanonicalType.FLOAT64,
    "long double":  CanonicalType.FLOAT128,
    "void":         CanonicalType.VOID,
    "_Bool":        CanonicalType.BOOLEAN,
    "bool":         CanonicalType.BOOLEAN,
    "unsigned int": CanonicalType.INT32,
    "unsigned char":CanonicalType.INT8,
    "unsigned long":CanonicalType.INT64,
    "size_t":       CanonicalType.INT64,
}

_IO_FUNCS = frozenset({"printf", "scanf", "fprintf", "fscanf", "fread", "fwrite",
                        "puts", "gets", "fgets", "fputs"})
_CONTROL_KW = frozenset({"if", "for", "while", "do", "switch", "return",
                          "break", "continue", "sizeof", "typeof"})


def _text(node: Node) -> str:
    """Decode node bytes to str."""
    return node.text.decode("utf-8", errors="replace") if node.text else ""


def _map_type(raw: str) -> CanonicalType:
    clean = raw.strip().rstrip("*").strip()
    # Remove qualifiers
    for qual in ("const ", "volatile ", "static ", "extern ", "inline ",
                 "restrict ", "unsigned ", "signed "):
        clean = clean.replace(qual, "")
    clean = clean.strip()
    return _C_TYPE_MAP.get(clean, CanonicalType.UNKNOWN)


# ── Node helpers ──────────────────────────────────────────────────────────────

def _child_by_type(node: Node, *types: str) -> Optional[Node]:
    for child in node.children:
        if child.type in types:
            return child
    return None


def _named_children(node: Node) -> List[Node]:
    return [c for c in node.children if c.is_named]


def _count_loc(source_bytes: bytes, start_byte: int, end_byte: int) -> int:
    chunk = source_bytes[start_byte:end_byte].decode("utf-8", errors="replace")
    count = 0
    in_block = False
    for line in chunk.splitlines():
        s = line.strip()
        if "/*" in s:
            in_block = True
        if "*/" in s:
            in_block = False
            continue
        if in_block:
            continue
        if s and not s.startswith("//"):
            count += 1
    return count


def _estimate_complexity(body_text: str) -> int:
    decisions = re.findall(r'\b(if|else\s+if|for|while|do|case|&&|\|\|)\b', body_text)
    return 1 + len(decisions)


# ── Return-type extraction ────────────────────────────────────────────────────

def _extract_return_type(func_def: Node) -> str:
    """
    In tree-sitter-c, function_definition children are:
        [type_specifier / ...] function_declarator compound_statement
    We want everything before the function_declarator.
    """
    parts: List[str] = []
    for child in func_def.children:
        if child.type in ("function_declarator", "pointer_declarator",
                          "compound_statement"):
            break
        if child.type not in ("comment",):
            parts.append(_text(child).strip())
    return " ".join(p for p in parts if p)


# ── Parameter extraction ──────────────────────────────────────────────────────

def _extract_params(declarator: Node) -> List[VariableIR]:
    """
    Walk function_declarator → parameter_list → parameter_declaration nodes.
    """
    params: List[VariableIR] = []
    param_list = _child_by_type(declarator, "parameter_list")
    if not param_list:
        return params

    for param in param_list.children:
        if param.type != "parameter_declaration":
            continue

        # Collect type tokens
        type_parts: List[str] = []
        param_name = ""
        for child in param.children:
            if child.type in ("identifier",):
                param_name = _text(child)
            elif child.type in ("primitive_type", "type_specifier",
                                 "sized_type_specifier", "type_identifier"):
                type_parts.append(_text(child))
            elif child.type in ("pointer_declarator",):
                # pointer param: name is deepest identifier
                inner = child
                while inner:
                    ident = _child_by_type(inner, "identifier")
                    if ident:
                        param_name = _text(ident)
                        break
                    inner = _child_by_type(inner, "pointer_declarator", "identifier")
                    if not inner:
                        break
                type_parts.append("*")
            elif child.type == "abstract_declarator":
                pass  # anonymous param like (void)

        raw_type = " ".join(type_parts).strip()
        if not param_name:
            param_name = f"_param{len(params)}"

        # In C,  foo(void)  means no parameters — skip the synthetic void entry
        if raw_type.strip().lower() == "void" and not param_name.isidentifier():
            continue
        if raw_type.strip().lower() == "void" and param_name.startswith("_param"):
            continue

        params.append(VariableIR(
            name=param_name,
            canonical_type=_map_type(raw_type),
            original_type_str=raw_type,
        ))

    return params


# ── Local variable extraction ─────────────────────────────────────────────────

def _extract_locals(compound: Node) -> List[VariableIR]:
    """Extract local variable declarations from a compound_statement."""
    locals_: List[VariableIR] = []
    for child in compound.children:
        if child.type == "declaration":
            _parse_declaration(child, locals_)
    return locals_


def _parse_declaration(decl_node: Node, out: List[VariableIR]) -> None:
    """Parse a single declaration node into VariableIR entries."""
    type_str = ""
    is_array = False
    dims: List[Tuple[int, int]] = []

    for child in decl_node.children:
        if child.type in ("primitive_type", "type_specifier",
                           "sized_type_specifier", "type_identifier"):
            type_str = _text(child)
        elif child.type == "init_declarator":
            _extract_declarator_name(child, type_str, is_array, dims, out)
        elif child.type in ("identifier",):
            # plain  int x;
            name = _text(child)
            if name and name not in ("const", "volatile", "static", "extern"):
                out.append(VariableIR(
                    name=name,
                    canonical_type=_map_type(type_str),
                    original_type_str=type_str,
                ))
        elif child.type == "array_declarator":
            is_array = True
            ident = _child_by_type(child, "identifier")
            if ident:
                out.append(VariableIR(
                    name=_text(ident),
                    canonical_type=_map_type(type_str),
                    original_type_str=type_str,
                    is_array=True,
                ))


def _extract_declarator_name(node: Node, type_str: str,
                              is_array: bool, dims: list,
                              out: List[VariableIR]) -> None:
    for child in node.children:
        if child.type == "identifier":
            out.append(VariableIR(
                name=_text(child),
                canonical_type=_map_type(type_str),
                original_type_str=type_str,
                is_array=is_array,
            ))
            return
        elif child.type in ("array_declarator",):
            ident = _child_by_type(child, "identifier")
            if ident:
                out.append(VariableIR(
                    name=_text(ident),
                    canonical_type=_map_type(type_str),
                    original_type_str=type_str,
                    is_array=True,
                ))
            return


# ── Call detection ────────────────────────────────────────────────────────────

def _find_calls(body_text: str, func_name: str) -> List[str]:
    all_calls = re.findall(r'\b(\w+)\s*\(', body_text)
    return list(set(
        c for c in all_calls
        if c != func_name and c not in _CONTROL_KW
    ))


# ── Function declarator unwrap ────────────────────────────────────────────────

def _unwrap_declarator(node: Node) -> Optional[Node]:
    """
    Handle  func_name(...)  and  *func_name(...)  (pointer return).
    Returns the function_declarator node.
    """
    if node.type == "function_declarator":
        return node
    if node.type == "pointer_declarator":
        inner = _child_by_type(node, "function_declarator", "pointer_declarator")
        if inner:
            return _unwrap_declarator(inner)
    return None


# ── Main parse entry ──────────────────────────────────────────────────────────

def parse_c_functions(source: str, filename: str = "<unknown>") -> List[FunctionIR]:
    """
    Parse C source with tree-sitter and return a list of FunctionIR.
    Returns [] on any error (caller should fall back to regex parser).
    """
    try:
        src_bytes = source.encode("utf-8", errors="replace")
        tree = _PARSER.parse(src_bytes)
        root = tree.root_node

        functions: List[FunctionIR] = []
        for node in root.children:
            if node.type != "function_definition":
                continue
            try:
                _process_function_def(node, src_bytes, functions)
            except Exception as exc:
                logger.debug("tree-sitter: skipping node in %s: %s", filename, exc)

        return functions

    except Exception as exc:
        logger.warning("tree-sitter C parse failed for %s: %s", filename, exc)
        return []


def _process_function_def(node: Node, src_bytes: bytes,
                           out: List[FunctionIR]) -> None:
    # Find declarator (may be wrapped in pointer_declarator for pointer-return)
    declarator_node: Optional[Node] = None
    compound_node: Optional[Node] = None

    for child in node.children:
        if child.type in ("function_declarator", "pointer_declarator"):
            declarator_node = _unwrap_declarator(child)
        elif child.type == "compound_statement":
            compound_node = child

    if not declarator_node or not compound_node:
        return

    # Function name: first identifier inside function_declarator
    func_name = ""
    for child in declarator_node.children:
        if child.type == "identifier":
            func_name = _text(child)
            break

    if not func_name or func_name in _CONTROL_KW:
        return

    # Return type
    ret_type_raw = _extract_return_type(node)
    ret_type = _map_type(ret_type_raw)

    # Parameters
    params = _extract_params(declarator_node)

    # Local variables
    local_vars = _extract_locals(compound_node)

    # Body text for heuristics
    body_text = _text(compound_node)
    body_start = compound_node.start_byte
    body_end = compound_node.end_byte

    loc = _count_loc(src_bytes, body_start, body_end)
    complexity = _estimate_complexity(body_text)
    calls = _find_calls(body_text, func_name)

    # Source lines (1-based)
    src_line_start = node.start_point[0] + 1
    src_line_end = node.end_point[0] + 1

    out.append(FunctionIR(
        name=func_name,
        source_language="C",
        kind="function",
        parameters=params,
        local_variables=local_vars,
        return_type=ret_type,
        calls=calls,
        source_line_start=src_line_start,
        source_line_end=src_line_end,
        loc=loc,
        cyclomatic_complexity=complexity,
        has_io=any(c in _IO_FUNCS for c in calls),
        has_loops=bool(re.search(r'\b(for|while|do)\s*\(', body_text)),
        has_conditionals=bool(re.search(r'\b(if|switch)\s*\(', body_text)),
    ))


def parse_c_globals(
    source: str,
    filename: str = "<unknown>",
) -> Tuple[List[VariableIR], List[VariableIR], List[str]]:
    """
    Parse global variables, #define constants, and #include headers.
    Returns (global_vars, constants, includes).
    """
    try:
        src_bytes = source.encode("utf-8", errors="replace")
        tree = _PARSER.parse(src_bytes)
        root = tree.root_node

        global_vars: List[VariableIR] = []
        constants: List[VariableIR] = []
        includes: List[str] = []

        for node in root.children:
            if node.type == "preproc_include":
                # #include <stdio.h> or "myfile.h"
                path_node = _child_by_type(node, "system_lib_string", "string_literal")
                if path_node:
                    raw = _text(path_node).strip("<>\"")
                    includes.append(raw)

            elif node.type == "preproc_def":
                # #define NAME value
                name_node = _child_by_type(node, "identifier")
                val_node  = _child_by_type(node, "preproc_arg")
                if name_node:
                    constants.append(VariableIR(
                        name=_text(name_node),
                        canonical_type=CanonicalType.UNKNOWN,
                        is_parameter=True,
                        initial_value=_text(val_node).strip() if val_node else None,
                        original_type_str="#define",
                    ))

            elif node.type == "declaration":
                # Global variable declaration
                _parse_declaration(node, global_vars)

        return global_vars, constants, includes

    except Exception as exc:
        logger.warning("tree-sitter global parse failed for %s: %s", filename, exc)
        return [], [], []
