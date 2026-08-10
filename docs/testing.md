# Testing Guide — RCI Code Equivalence Platform

## Test Structure

```
backend/tests/
├── conftest.py              ← Shared fixtures (in-memory SQLite, HTTPX async client)
├── test_health.py           ← Health and system-info endpoint tests
├── test_compiler_detection.py ← Compiler detection unit tests
└── test_ir_models.py        ← IR models, analyzers, comparison, gap detection
```

## Running Tests

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest -v
```

## Test Coverage

### Phase 1 Tests (Currently Active)

| Test | What It Verifies |
|------|-----------------|
| `test_health_returns_200` | Backend liveness |
| `test_health_response_structure` | offline=true, version, timestamp fields |
| `test_status_endpoint` | Uptime, compiler booleans |
| `test_system_info_endpoint` | OS, Python, compiler lists |
| `test_system_info_has_disk_info` | Real disk usage |
| `test_process_time_header_present` | Middleware working |
| `test_detect_nonexistent_compiler` | NOT_FOUND status |
| `test_detect_compiler_with_invalid_override` | ERROR status |
| `test_compiler_info_fields` | Dataclass structure |
| `test_detect_all_compilers_returns_result` | Always returns result |
| `test_detection_result_properties` | Boolean properties |
| `test_detect_compiler_with_mocked_path` | DETECTED status with mock |
| `test_program_ir_function_names` | IR function list |
| `test_program_ir_get_function` | IR lookup |
| `test_variable_ir_array` | Array dimensions |
| `test_c_analyzer_finds_functions` | C parser detects functions |
| `test_c_analyzer_detects_includes` | #include extraction |
| `test_c_analyzer_detects_defines` | #define extraction |
| `test_c_analyzer_counts_lines` | LOC counting |
| `test_fortran_analyzer_finds_program` | Fortran parser detects PROGRAM |
| `test_fortran_analyzer_detects_io` | WRITE detection |
| `test_fortran_analyzer_detects_implicit_none` | IMPLICIT NONE detection |
| `test_name_similarity_exact` | Exact name match = 1.0 |
| `test_name_similarity_partial` | Partial match in range |
| `test_name_similarity_different` | Different names < 0.5 |
| `test_compare_programs_identical_names` | Comparison produces result |
| `test_gap_detection_missing_implicit_none` | INITIALIZATION_MISMATCH gap |
| `test_gap_detection_produces_ids` | GAP-XXX sequential IDs |
| `test_gap_to_dict_has_required_fields` | All required fields in dict |

### Planned Tests (Phase 14)

- Integration: C compile → execute → output capture
- Integration: Fortran compile → execute → output capture
- End-to-end: upload → analyze → compare → gaps → execute → compare → report
- Negative: invalid C syntax, compilation failure, timeout, malformed output
- Numerical: absolute tolerance, relative tolerance, floating-point edge cases

## Test Philosophy

1. **No fake results** — all tests verify actual computation
2. **Isolated test DB** — in-memory SQLite, no state between tests
3. **Mock only where necessary** — compiler detection mocked when compiler unavailable
4. **Negative tests are first-class** — invalid inputs, missing compilers, timeouts

## Adding New Tests

```python
# backend/tests/test_your_feature.py

import pytest

@pytest.mark.asyncio
async def test_something(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
```
