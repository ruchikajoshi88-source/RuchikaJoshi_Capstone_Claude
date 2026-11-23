# SCRUM-7 — Verification Report

- Stage: 7 of 8 (agent: automation-tester)
- Date: 2026-11-23
- Branch / commit under test: `feature/SCRUM-7-task-management-api` @ 6557a67 (working tree clean for `src/` and `tests/`)
- Environment: Windows 11, Python 3.13.14, pytest 9.2.0, FastAPI 0.165.0, Starlette 1.10.0, SQLAlchemy 2.1.9, Pydantic 2.14.4, httpx 0.28.1
- **Result: PASS — 53 passed, 0 failed, 0 errors, 1 warning**

All numbers below come from commands executed in this session; nothing is estimated.

## 1. Test Execution

| Command | Exit | Result |
|---------|------|--------|
| `.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider` | 0 | `53 passed, 1 warning in 0.97s` |
| `pytest -q -p no:cacheprovider` (bare `pytest` on PATH from `.venv/Scripts`) | 0 | `53 passed, 1 warning in 1.27s` |

Per-module results (all PASSED):

| Module | Tests |
|--------|-------|
| `tests/test_tasks_create.py` | 8 |
| `tests/test_tasks_read.py` | 4 |
| `tests/test_tasks_update.py` | 7 |
| `tests/test_tasks_delete.py` | 5 |
| `tests/test_tasks_validation.py` | 29 |
| **Total** | **53** |

Header of the verbose run (verbatim):
```
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\ruchika_joshi\Desktop\Capstone Claude
configfile: pytest.ini
testpaths: tests
collected 53 items
...
======================== 53 passed, 1 warning in 0.97s ========================
```

Warning (non-failing, verbatim summary): `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

Isolation check: `src/tasks.db` did not exist after any pytest run.

## 2. Acceptance Criteria Traceability

| AC | Criterion | Passing tests (module::name) | Status |
|----|-----------|------------------------------|--------|
| AC-1 | Valid create returns 201 with object incl. generated `id` | create::`test_create_returns_201_with_generated_id`, `test_create_defaults_status_to_todo`, `test_create_accepts_each_allowed_status[x3]`, `test_create_assigns_increasing_ids`, `test_create_accepts_empty_description`, `test_create_strips_surrounding_whitespace_from_title` | PASS |
| AC-2 | List returns 200 with JSON array | read::`test_list_is_empty_array_when_no_tasks`, `test_list_returns_all_tasks_ordered_by_id` | PASS |
| AC-3 | Get existing 200; missing 404 with exact detail | read::`test_get_existing_task_returns_200`, `test_get_missing_task_returns_404_with_exact_detail` | PASS |
| AC-4 | PATCH updates only provided fields, 200; missing 404 | update::`test_patch_title_only_...`, `..._status_only_...`, `..._description_only_...`, `test_patch_all_fields`, `test_patch_empty_body_returns_task_unchanged`, `test_patch_missing_task_returns_404_with_exact_detail`, `test_patch_change_persists_on_subsequent_get` | PASS |
| AC-5 | DELETE removes row, 204; missing 404 | delete::`test_delete_existing_task_returns_204_with_empty_body`, `test_deleted_task_is_gone_from_get_and_list`, `test_delete_missing_task_returns_404_with_exact_detail`, `test_delete_twice_returns_404_the_second_time`, `test_ids_are_not_reused_after_deleting_the_newest_task` | PASS |
| AC-6 | Happy-path and error-handling tests pass via `pytest` | Whole suite: 53 passed (section 1) | PASS |

Functional requirements:

| FR | Evidence | Status |
|----|----------|--------|
| FR-001..FR-005 | AC-1..AC-5 tests, live smoke test (section 3) | PASS |
| FR-006 auto-increment ID | increasing-ids test, no-reuse test, live run (IDs 1, 2, then 3 after deleting 2) | PASS |
| FR-007 status enum + default | `[todo,in_progress,done]` accepted, default `todo`, `blocked`/`null` rejected (validation module) | PASS |
| FR-008 404 message | exact `{"detail": "Task with ID {id} does not exist"}` asserted for GET/PATCH/DELETE, including out-of-range IDs (9 tests) | PASS |

Approved defaults Q-1..Q-7 are each covered by a validation test (422 for bad input, whitespace-only title, `{}` PATCH ok, `null` PATCH rejected, order by id, non-integer id 422).

## 3. Live Smoke Test (production startup path)
`uvicorn src.main:app --port 8765` was started for real (this exercises the `lifespan` / `create_all` path and the on-disk `src/tasks.db`, which pytest deliberately does not). Responses observed:

| Request | Observed |
|---------|----------|
| `POST /tasks {"title":"Smoke","description":"live"}` | 201 `{"id":1,...,"status":"todo"}` |
| `POST /tasks` with `status: in_progress` | 201 `id` 2 |
| `GET /tasks` | 200, array of 2 |
| `GET /tasks/1` | 200 |
| `PATCH /tasks/1 {"status":"done"}` | 200, status `done`, other fields unchanged |
| `DELETE /tasks/2` | 204, empty body |
| `GET /tasks/2` | 404 `{"detail":"Task with ID 2 does not exist"}` |
| `POST /tasks {"title":"",...}` | 422 |
| `GET /tasks/99999999999999999999` | 404 with exact message (was 500 before CR-1 fix) |
| `POST /tasks` after deleting id 2 | 201 `id` 3 (ID not reused) |

The server was then stopped (confirmed no listener) and the generated `src/tasks.db` was deleted (it is git-ignored).

## 4. Test Quality Evidence
- Mutation check for CR-1: with the `crud.py` fix reverted, `9 failed, 44 passed`; with the fix, `53 passed`. The new tests detect the defect they target.
- Independent reviewer (fresh agent) found no vacuous assertions; see code-review.md.
- Limitation: the suite passed on its first run (43/43) before CR-1 tests were added; only CR-1 was mutation-checked. Other tests were not individually mutation-tested.

## 5. Not Verified / Known Gaps
- No coverage tool was run; coverage percentage is not reported.
- No load, concurrency, or cross-platform testing (single-user scope).
- No linter/type-checker is configured in the project, so none was run.
- GitHub push / PR creation is Stage 8 and not yet performed.

## 6. Conclusion
All acceptance criteria AC-1..AC-6 and requirements FR-001..FR-008 are verified by real test execution plus a live server run. No open defects. Ready for Stage 8, subject to the final human approval gate.
