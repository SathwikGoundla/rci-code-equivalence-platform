# Algorithm — RCI Code Equivalence Platform

## Phase 1: Structural Analysis Algorithm

### C Structural Extraction

```
INPUT: C source code (string)
OUTPUT: ProgramIR

1. Scan for #include directives → includes[]
2. Scan for #define macros → constants[]
3. Detect global variable declarations (outside braces) → global_variables[]
4. For each function signature match:
   a. Extract return type → map to CanonicalType
   b. Extract function name
   c. Extract parameter list → parse into VariableIR[]
   d. Find matching closing brace (brace depth counter)
   e. Extract function body
   f. Compute LOC (non-blank, non-comment lines)
   g. Estimate cyclomatic complexity (count IF/FOR/WHILE/CASE/&&/||)
   h. Detect I/O calls (printf/scanf/fprintf)
   i. Detect loop patterns (for/while/do)
   j. Detect conditional patterns (if/switch)
   k. Detect function calls within body
   l. Emit FunctionIR
5. Return ProgramIR with all extracted data
```

### Fortran Structural Extraction

```
INPUT: Fortran source code (string)
OUTPUT: ProgramIR

1. Scan for USE statements → includes[]
2. Scan for MODULE definitions → modules[]
3. Scan for PARAMETER declarations → constants[]
4. For each PROGRAM / FUNCTION / SUBROUTINE match:
   a. Extract unit name and kind
   b. Extract parameter list
   c. Find END [unit] statement
   d. Extract body
   e. Check for IMPLICIT NONE → has_implicit_none
   f. Compute LOC
   g. Estimate cyclomatic complexity (IF/ELSE IF/DO/.AND./.OR.)
   h. Detect WRITE/READ/PRINT → has_io
   i. Detect DO loops → has_loops
   j. Detect IF blocks → has_conditionals
   k. Detect CALL statements → calls[]
   l. Emit FunctionIR
5. Return ProgramIR
```

### IR Comparison Algorithm

```
INPUT: c_ir: ProgramIR, fortran_ir: ProgramIR
OUTPUT: ComparisonResult

For each C function cf:
  best_match = None
  best_score = 0.0

  For each Fortran function ff (not yet matched):
    score = levenshtein_similarity(cf.name, ff.name)
    if score > best_score:
      best_match = ff
      best_score = score

  if best_match and best_score >= 0.6:
    Emit MATCHED pair with:
      - parameter count comparison
      - return type comparison
      - cyclomatic complexity delta
      - I/O presence comparison
      - loop presence comparison
  else:
    Emit C_ONLY gap

For remaining unmatched Fortran functions:
  Emit FORTRAN_ONLY gap

Structural score = 2 * Σ(match_similarity) / (|C functions| + |Fortran functions|)
```

### Gap Detection Rules

| Gap Category | Trigger Condition | Severity | Confidence |
|---|---|---|---|
| missing_function | C function with no Fortran counterpart | HIGH | 0.85 |
| missing_subroutine | Fortran unit with no C counterpart | HIGH | 0.85 |
| type_mismatch | Return types differ between matched pair | MEDIUM | 0.90 |
| missing_variable | Parameter count differs | HIGH | 0.88 |
| precision_mismatch | FLOAT32 ↔ FLOAT64 or INT32 ↔ INT64 | MEDIUM | 0.91 |
| different_output_handling | C has I/O, Fortran does not | LOW | 0.75 |
| different_input_handling | Fortran has I/O, C does not | LOW | 0.75 |
| missing_branch | Cyclomatic complexity delta > 3 | MEDIUM | 0.70 |
| missing_loop | One has loops, other does not | HIGH | 0.82 |
| initialization_mismatch | Fortran missing IMPLICIT NONE | LOW | 0.95 |

## Phase 3+ (Planned): AST-Based Analysis

Will use:
- **tree-sitter + tree-sitter-c**: Full C AST, exact type resolution, macro expansion
- **fparser2**: Full Fortran AST, COMMON blocks, EQUIVALENCE, array specs

## Numerical Comparison Algorithm (Phase 10)

```
For each output value pair (c_val, f_val):
  abs_diff = |c_val - f_val|
  rel_diff = abs_diff / max(|f_val|, epsilon)

  if abs_diff <= atol + rtol * |f_val|:
    result = PASS
  elif abs_diff <= 1e-3:
    result = PASS_WITH_NUMERICAL_DIFFERENCE
  else:
    result = FAIL
```
