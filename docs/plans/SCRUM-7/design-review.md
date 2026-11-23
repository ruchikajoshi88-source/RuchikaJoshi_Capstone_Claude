# SCRUM-7 — Design Review

- Stage: 3 of 8 (agent: solution-engineer)
- Reviewed: docs/plans/SCRUM-7/architecture.md against docs/plans/SCRUM-7/requirements.md, CLAUDE.md constraints, and the installed environment
- Verdict: **APPROVED WITH CHANGES** (all changes already applied to architecture.md; no open blockers for design)

## 1. Scope and Constraint Check

| Check | Result |
|-------|--------|
| Covers FR-001..FR-008 and AC-1..AC-6 | Pass (traceability table, architecture section 9) |
| Stack limited to FastAPI, SQLAlchemy, SQLite, Pydantic v2, Pytest | Pass; `httpx` is only the TestClient dependency |
| No extra services / cloud / frameworks | Pass (no Alembic, no async driver, no auth) |
| No fields beyond story data model | Pass (no timestamps) |
| Approved defaults Q-1..Q-10 reflected | Pass (422, empty description allowed, strip title, `{}` PATCH ok, `null` rejected, ordered by id, `src/tasks.db`) |
| No secrets in design | Pass |

## 2. Findings

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| D-1 | Medium | Draft design said ID reuse after deleting the newest row was acceptable. SQLAlchemy does not emit SQLite `AUTOINCREMENT` for a plain integer PK, so a deleted task's ID could later refer to a different task. FR-006 says "auto-incremented"; reuse is surprising for a REST resource. | Applied: `__table_args__ = {"sqlite_autoincrement": True}`; added a test case (architecture 3, A-R2). |
| D-2 | Low | Optional `TASKS_DATABASE_URL` env override was not required by the story or by test design (tests use dependency override). Extra config surface. | Applied: removed; `DATABASE_URL` is a constant (architecture 5). |
| D-3 | Medium | Draft claimed pytest would put the repo root on `sys.path` via the root `conftest.py`. With `tests/` lacking `__init__.py`, `prepend` mode inserts `tests/`, so `from src.main import app` would fail on plain `pytest` once the root `conftest.py` is removed. | Applied: add `pytest.ini` (`pythonpath = .`, `testpaths = tests`), delete root `conftest.py` (architecture 2, ADR-5). |
| D-4 | Info | `crud.py` plus `routers/tasks.py` is slightly more structure than a five-endpoint API strictly needs. | Accepted: small files, clean 404 boundary, no extra dependency. Do not add services/repositories layers beyond this. |
| D-5 | Info | Explicit-`null` rejection on PATCH makes OpenAPI show `str \| null` for update fields. | Accepted: documented behaviour (Q-4); covered by a validation test. |
| D-6 | Info | Pydantic strips before length checks, so a whitespace-only title yields `min_length` failure (422) as intended. | Accepted; must be proven by a test (not assumed). |
| D-7 | Info | A 204 handler must send no body. | Accepted; implement with `status_code=204` and return `None`/`Response`, and assert `response.content == b""` in the test. |

## 3. Security Review (design level)
- All DB access via ORM parameter binding; no raw SQL strings.
- Inputs bounded: title max 255; status enum; id integer. `description` is unbounded text per the story (acceptable; no request-size middleware is in scope).
- Existing repo issue R-1 (token in `.env.example`) is not a design flaw but remains a blocker for the commit/PR stage. It is carried into the implementation plan as a gating task.

## 4. Testability Review
- In-memory SQLite with `StaticPool` plus dependency override gives isolated tests and avoids creating `src/tasks.db`.
- `TestClient` is used without a context manager so the production lifespan does not run; a fixture comment/assertion will make that explicit.
- Every AC has at least one mapped test (requirements section 5); added cases: ID non-reuse (D-1), empty-body 204 (D-7), whitespace-only title (D-6).

## 5. Residual Risks (accepted)
- Newer library versions than the `>=` floors (SQLAlchemy 2.1, Starlette 1.x); mitigated by using only stable 2.0-style APIs and by running the real test suite in Stage 7.
- No concurrency control on PATCH (single-user scope).

## 6. Decision
Proceed to Stage 4 (Implementation Planning). No further human gate between Stage 3 and Stage 4.
