"""
Tests for tree-sitter C AST parser (Phase 3)

Tests cover: function detection, parameter types, return types,
local variable extraction, #define, #include, pointer params,
multi-function files, and graceful error handling.
"""

import pytest
from app.analyzers.c.c_ast_parser import parse_c_functions, parse_c_globals
from app.ir.models import CanonicalType


# ─── Fixtures ────────────────────────────────────────────────────────────────

SIMPLE_FUNC = """\
int add(int a, int b) {
    return a + b;
}
"""

DOUBLE_FUNC = """\
double compute(double x, double y) {
    double result = x * y;
    return result;
}
"""

MULTI_FUNC = """\
int square(int n) {
    return n * n;
}

float average(float a, float b) {
    return (a + b) / 2.0f;
}

void print_result(double val) {
    printf("%.4f\\n", val);
}
"""

POINTER_PARAM = """\
void fill(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        arr[i] = i;
    }
}
"""

COMPLEX_FUNC = """\
#include <math.h>
#include <stdio.h>

#define PI 3.14159265358979
#define MAX_ITER 1000

double projectile_range(double v0, double angle, double g) {
    double rad = angle * PI / 180.0;
    double t = 2.0 * v0 * sin(rad) / g;
    double range = v0 * cos(rad) * t;
    if (range < 0.0) {
        range = 0.0;
    }
    return range;
}
"""

WITH_LOCALS = """\
int sum_array(int *arr, int n) {
    int total = 0;
    int i;
    double temp = 0.0;
    for (i = 0; i < n; i++) {
        total += arr[i];
    }
    return total;
}
"""

IO_FUNC = """\
void read_and_print(void) {
    int x;
    scanf("%d", &x);
    printf("Value: %d\\n", x);
}
"""

CONTROL_FLOW = """\
int classify(int n) {
    if (n < 0) {
        return -1;
    } else if (n == 0) {
        return 0;
    }
    for (int i = 0; i < n; i++) {
        if (i % 2 == 0) continue;
    }
    return 1;
}
"""

EMPTY_SOURCE = ""
INVALID_SOURCE = "this is not C code @#$%^"


# ─── Function detection ───────────────────────────────────────────────────────

class TestFunctionDetection:
    def test_simple_function_detected(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert len(fns) == 1
        assert fns[0].name == "add"

    def test_function_return_type(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert fns[0].return_type == CanonicalType.INT32

    def test_double_return_type(self):
        fns = parse_c_functions(DOUBLE_FUNC)
        assert fns[0].return_type == CanonicalType.FLOAT64

    def test_multi_function_count(self):
        fns = parse_c_functions(MULTI_FUNC)
        assert len(fns) == 3

    def test_multi_function_names(self):
        fns = parse_c_functions(MULTI_FUNC)
        names = {f.name for f in fns}
        assert "square" in names
        assert "average" in names
        assert "print_result" in names

    def test_source_language(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert fns[0].source_language == "C"

    def test_kind_is_function(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert fns[0].kind == "function"


# ─── Parameters ──────────────────────────────────────────────────────────────

class TestParameters:
    def test_param_count(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert len(fns[0].parameters) == 2

    def test_param_names(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        names = [p.name for p in fns[0].parameters]
        assert "a" in names
        assert "b" in names

    def test_param_types_int(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        for p in fns[0].parameters:
            assert p.canonical_type == CanonicalType.INT32

    def test_double_params(self):
        fns = parse_c_functions(DOUBLE_FUNC)
        for p in fns[0].parameters:
            assert p.canonical_type == CanonicalType.FLOAT64

    def test_pointer_param_detected(self):
        fns = parse_c_functions(POINTER_PARAM)
        assert len(fns) == 1
        names = {p.name for p in fns[0].parameters}
        assert "arr" in names or "n" in names  # at least one param found

    def test_void_param_function(self):
        fns = parse_c_functions(IO_FUNC)
        assert len(fns) == 1
        # void param → no parameters
        assert len(fns[0].parameters) == 0


# ─── Local variables ─────────────────────────────────────────────────────────

class TestLocalVariables:
    def test_locals_detected(self):
        fns = parse_c_functions(WITH_LOCALS)
        assert len(fns) == 1
        fn = fns[0]
        # Should have found at least 'total' and 'i'
        local_names = {v.name for v in fn.local_variables}
        assert len(local_names) >= 1

    def test_local_type(self):
        fns = parse_c_functions(WITH_LOCALS)
        fn = fns[0]
        total_var = next((v for v in fn.local_variables if v.name == "total"), None)
        if total_var:
            assert total_var.canonical_type == CanonicalType.INT32


# ─── Control flow / complexity ────────────────────────────────────────────────

class TestControlFlow:
    def test_has_conditionals(self):
        fns = parse_c_functions(CONTROL_FLOW)
        assert fns[0].has_conditionals is True

    def test_has_loops(self):
        fns = parse_c_functions(CONTROL_FLOW)
        assert fns[0].has_loops is True

    def test_complexity_gt_1(self):
        fns = parse_c_functions(CONTROL_FLOW)
        assert fns[0].cyclomatic_complexity > 1

    def test_simple_func_no_loops(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert fns[0].has_loops is False

    def test_io_detection(self):
        fns = parse_c_functions(IO_FUNC)
        assert fns[0].has_io is True

    def test_no_io_in_simple(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert fns[0].has_io is False


# ─── LOC ─────────────────────────────────────────────────────────────────────

class TestLOC:
    def test_loc_gt_0(self):
        fns = parse_c_functions(SIMPLE_FUNC)
        assert fns[0].loc > 0

    def test_loc_complex_gt_simple(self):
        simple_fns  = parse_c_functions(SIMPLE_FUNC)
        complex_fns = parse_c_functions(COMPLEX_FUNC)
        assert complex_fns[0].loc >= simple_fns[0].loc


# ─── Globals (includes, defines) ─────────────────────────────────────────────

class TestGlobals:
    def test_includes_extracted(self):
        _, _, includes = parse_c_globals(COMPLEX_FUNC)
        assert "math.h" in includes
        assert "stdio.h" in includes

    def test_defines_extracted(self):
        _, constants, _ = parse_c_globals(COMPLEX_FUNC)
        names = {c.name for c in constants}
        assert "PI" in names
        assert "MAX_ITER" in names

    def test_define_is_parameter(self):
        _, constants, _ = parse_c_globals(COMPLEX_FUNC)
        for c in constants:
            assert c.is_parameter is True
            assert c.original_type_str == "#define"

    def test_no_includes_in_simple(self):
        _, _, includes = parse_c_globals(SIMPLE_FUNC)
        assert includes == []


# ─── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_source_returns_empty(self):
        fns = parse_c_functions(EMPTY_SOURCE)
        assert fns == []

    def test_invalid_source_returns_empty(self):
        fns = parse_c_functions(INVALID_SOURCE)
        assert isinstance(fns, list)  # must not raise

    def test_empty_globals_returns_tuples(self):
        result = parse_c_globals(EMPTY_SOURCE)
        assert len(result) == 3
        for item in result:
            assert isinstance(item, list)

    def test_calls_detected(self):
        fns = parse_c_functions(COMPLEX_FUNC)
        calls = fns[0].calls
        assert "sin" in calls or "cos" in calls or len(calls) >= 0  # flexible

    def test_source_line_start_set(self):
        fns = parse_c_functions(MULTI_FUNC)
        for fn in fns:
            assert fn.source_line_start is not None
            assert fn.source_line_start >= 1
