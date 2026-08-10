"""
Common Intermediate Representation (IR) Models

Language-independent representation of C and Fortran programs.
Both C and Fortran source get parsed into these structures before comparison.

Design principles:
- Uses 0-based logical array indices (normalized from Fortran 1-based)
- Control flow is represented as a directed graph of BasicBlocks
- All types are normalized to a canonical set
- Ambiguous mappings are flagged with a confidence score
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ── Canonical Types ────────────────────────────────────────────────────────────

class CanonicalType(str, Enum):
    """Language-independent type system."""
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"   # C float / Fortran REAL
    FLOAT64 = "float64"   # C double / Fortran DOUBLE PRECISION
    FLOAT128 = "float128" # Fortran REAL(16) / C long double
    COMPLEX64 = "complex64"
    COMPLEX128 = "complex128"
    BOOLEAN = "boolean"
    CHARACTER = "character"
    STRING = "string"
    VOID = "void"
    UNKNOWN = "unknown"


# ── Operators ──────────────────────────────────────────────────────────────────

class BinaryOp(str, Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    POW = "pow"
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    AND = "and"
    OR = "or"
    NOT = "not"
    BAND = "bitand"
    BOR = "bitor"
    BXOR = "bitxor"
    SHL = "shl"
    SHR = "shr"


# ── Expressions ───────────────────────────────────────────────────────────────

class LiteralExpr(BaseModel):
    kind: str = "literal"
    value: Any
    canonical_type: CanonicalType


class VariableRefExpr(BaseModel):
    kind: str = "var_ref"
    name: str
    canonical_type: CanonicalType


class BinaryExpr(BaseModel):
    kind: str = "binary"
    op: BinaryOp
    left: Any  # Expr
    right: Any  # Expr
    canonical_type: CanonicalType


class CallExpr(BaseModel):
    kind: str = "call"
    function_name: str
    arguments: List[Any]  # List[Expr]
    canonical_type: CanonicalType


class ArrayAccessExpr(BaseModel):
    kind: str = "array_access"
    array_name: str
    # Indices are normalized to 0-based logical offsets
    indices: List[Any]  # List[Expr]
    canonical_type: CanonicalType
    original_base_index: int = 0  # 0 for C, 1 for Fortran (before normalization)


# ── Statements ────────────────────────────────────────────────────────────────

class AssignStatement(BaseModel):
    kind: str = "assign"
    target: Any  # Expr (variable or array access)
    value: Any   # Expr
    source_line: Optional[int] = None


class ReturnStatement(BaseModel):
    kind: str = "return"
    value: Optional[Any] = None  # Expr or None
    source_line: Optional[int] = None


class LoopIR(BaseModel):
    """Normalized representation of DO loops and for/while loops."""
    kind: str = "loop"
    loop_variable: Optional[str] = None
    start: Optional[Any] = None    # Expr
    stop: Optional[Any] = None     # Expr
    step: Optional[Any] = None     # Expr (default 1)
    body: List[Any] = Field(default_factory=list)  # List[Statement]
    loop_type: str = "count"       # "count" | "while" | "do_while"
    source_line: Optional[int] = None


class ConditionalIR(BaseModel):
    """Normalized IF/ELSE/SELECT CASE."""
    kind: str = "conditional"
    condition: Any  # Expr
    then_body: List[Any] = Field(default_factory=list)
    else_body: List[Any] = Field(default_factory=list)
    source_line: Optional[int] = None


class IOStatement(BaseModel):
    """READ/WRITE/PRINT/scanf/printf."""
    kind: str = "io"
    direction: str  # "read" | "write"
    format_str: Optional[str] = None
    variables: List[str] = Field(default_factory=list)
    source_line: Optional[int] = None


# ── Variables and Parameters ───────────────────────────────────────────────────

class VariableIR(BaseModel):
    name: str
    canonical_type: CanonicalType
    is_array: bool = False
    array_dimensions: Optional[List[Tuple[int, int]]] = None  # [(low, high), ...]
    is_parameter: bool = False     # Fortran PARAMETER / C const
    initial_value: Optional[Any] = None
    is_intent_in: bool = False     # Fortran INTENT(IN)
    is_intent_out: bool = False    # Fortran INTENT(OUT)
    source_line: Optional[int] = None
    original_type_str: str = ""   # Raw type string from source


# ── Function / Subroutine IR ──────────────────────────────────────────────────

class FunctionIR(BaseModel):
    """
    Normalized representation of a C function or Fortran FUNCTION/SUBROUTINE.
    """
    name: str
    source_language: str          # "C" | "Fortran"
    kind: str = "function"        # "function" | "subroutine" | "program"
    parameters: List[VariableIR] = Field(default_factory=list)
    local_variables: List[VariableIR] = Field(default_factory=list)
    return_type: Optional[CanonicalType] = None
    body: List[Any] = Field(default_factory=list)  # List[Statement]
    calls: List[str] = Field(default_factory=list)  # function names called
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    loc: int = 0                  # lines of code
    cyclomatic_complexity: int = 1

    # Analysis annotations
    has_implicit_none: bool = False   # Fortran specific
    has_io: bool = False
    has_loops: bool = False
    has_conditionals: bool = False
    array_accesses: List[str] = Field(default_factory=list)


# ── Program IR ────────────────────────────────────────────────────────────────

class ProgramMetadata(BaseModel):
    filename: str
    source_language: str   # "C" | "Fortran"
    language_standard: str = ""  # e.g. "C99", "F2003"
    total_lines: int = 0
    total_loc: int = 0
    parse_warnings: List[str] = Field(default_factory=list)
    parse_errors: List[str] = Field(default_factory=list)
    parser_used: str = ""  # "tree-sitter" | "pycparser" | "fparser2" | "regex"


class ProgramIR(BaseModel):
    """
    Top-level intermediate representation for a complete C or Fortran program.
    This is what the comparison engine operates on.
    """
    metadata: ProgramMetadata
    functions: List[FunctionIR] = Field(default_factory=list)
    global_variables: List[VariableIR] = Field(default_factory=list)
    constants: List[VariableIR] = Field(default_factory=list)  # PARAMETER / #define
    includes: List[str] = Field(default_factory=list)          # #include / USE
    modules: List[str] = Field(default_factory=list)           # Fortran MODULEs

    @property
    def function_names(self) -> List[str]:
        return [f.name for f in self.functions]

    @property
    def function_count(self) -> int:
        return len(self.functions)

    def get_function(self, name: str) -> Optional[FunctionIR]:
        return next((f for f in self.functions if f.name == name), None)
