# SCRUM-7 — Task Management REST API: Requirements Analysis

- Workflow ID: sdlc-SCRUM-7-20261123
- Source: https://ruchikajoshi88.atlassian.net/browse/SCRUM-7 (Story, Priority: Medium, Status: To Do, no comments, no linked issues)
- Stage: 1 of 8 — Requirements Analysis (agent: business-analyst)
- Status: DRAFT — awaiting human approval

## 1. User Story
As a user, I want to create, view, update, and delete tasks via a REST API, so that I can manage my daily activities.

## 2. Scope
In scope: a single `tasks` resource with CRUD over HTTP, persisted in SQLite, built with FastAPI, SQLAlchemy, Pydantic v2, tested with Pytest.
Out of scope (not in the story, not to be added): authentication, users/ownership, pagination, filtering, sorting, timestamps, due dates, priorities, `PUT` (full replace), Docker/cloud setup, migrations tooling, extra frameworks.

## 3. Functional Requirements

| ID | Requirement | Endpoint | Success response |
|----|-------------|----------|------------------|
| FR-001 | Create a task with title, description, status | `POST /tasks` | `201 Created` + task object with generated `id` |
| FR-002 | Return a list of all tasks | `GET /tasks` | `200 OK` + JSON array |
| FR-003 | Return one task by ID | `GET /tasks/{id}` | `200 OK` + task object |
| FR-004 | Partially update title, description, or status | `PATCH /tasks/{id}` | `200 OK` + updated task; only provided fields change |
| FR-005 | Delete a task by ID | `DELETE /tasks/{id}` | `204 No Content`, empty body |
| FR-006 | Each task has a system-assigned auto-incremented integer ID | — | — |
| FR-007 | Status restricted to `todo`, `in_progress`, `done`; defaults to `todo` on create if omitted | — | — |
| FR-008 | Unknown task ID returns `404 Not Found` with detail `"Task with ID {id} does not exist"` | `GET`/`PATCH`/`DELETE /tasks/{id}` | — |

## 4. Data Model (`tasks` table, SQLite)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | integer | System | Primary key, auto-increment |
| `title` | string (max 255) | Yes | Non-empty |
| `description` | text | Yes | Task description |
| `status` | string (max 20) | Yes | `todo` / `in_progress` / `done`; default `todo` |

## 5. Acceptance Criteria (from Jira) with test traceability

| AC | Criterion | Maps to | Planned test cases |
|----|-----------|---------|--------------------|
| AC-1 | Valid create returns 201 with created object incl. generated `id` | FR-001, FR-006 | create returns 201 and `id`; default status is `todo`; ids increment |
| AC-2 | List returns 200 with JSON array of stored tasks | FR-002 | empty list `[]`; list after creating N tasks |
| AC-3 | Get existing returns 200; non-existent returns 404 with exact detail | FR-003, FR-008 | get existing; get missing -> 404 + exact message |
| AC-4 | PATCH updates only provided fields, returns 200; non-existent returns 404 | FR-004, FR-008 | patch single field leaves others unchanged; patch missing -> 404 |
| AC-5 | DELETE removes from SQLite, returns 204; non-existent returns 404 | FR-005, FR-008 | delete then GET -> 404; delete missing -> 404 |
| AC-6 | Happy-path and error-handling tests pass via `pytest` | all | full suite green, actual run output reported |

Additional validation cases implied by FR-007 / data model (assumptions A-3 to A-6 below): invalid status rejected; empty title rejected; title > 255 chars rejected.

## 6. Non-Functional / Constraints
- Stack fixed by CLAUDE.md: FastAPI, SQLAlchemy, SQLite, Pydantic v2, Pytest. No additional frameworks or services.
- Tests must be isolated from the real database file (temporary or in-memory SQLite).
- No secrets in source, docs, or `.mcp.json`.

## 7. Current Repository State (observed)
- `src/` and `tests/` exist but are empty; no application code yet.
- `requirements.txt`, `requirements-test.txt`, `conftest.py` (adds `src/` to `sys.path`), `.venv/`, `.env.example` exist.
- `README.md` says run command is `uvicorn src.main:app --reload`; it also contains stray shell text (`Set-Content -Encoding UTF8 CLAUDE.md`) from a copy/paste error.
- Git: branch `main` has no commits and no remote configured.
- `.mcp.json` points the sqlite MCP server at `./src/tasks.db`; that server failed to connect this session (non-blocking for this story).

## 8. Ambiguities and Clarification Questions

Each item has a proposed default. If you approve without comment, the defaults apply.

| # | Question | Proposed default |
|---|----------|------------------|
| Q-1 | Validation failures: the story only defines 404. Which status code for invalid input (bad status, empty title, wrong types)? | FastAPI/Pydantic default `422 Unprocessable Entity`. |
| Q-2 | Is `description` mandatory on create? The data model says Required = Yes, but FR-007 only gives a default for `status`. Can it be an empty string? | `description` required on `POST`, empty string allowed. `title` must be non-empty. |
| Q-3 | Is a whitespace-only title "non-empty"? | Strip whitespace; whitespace-only title is rejected (422). |
| Q-4 | `PATCH` with an empty body `{}` or with explicit `null` values? | `{}` returns 200 with the task unchanged. `null` for `title`/`description`/`status` is rejected (422) because those columns are required. |
| Q-5 | `GET /tasks` ordering? | Ascending by `id`. No pagination or filtering. |
| Q-6 | Non-integer ID in path (e.g. `/tasks/abc`)? | `422` from FastAPI path validation. |
| Q-7 | Should responses include `created_at`/`updated_at`? | No. The story's data model has only 4 fields. |
| Q-8 | Module layout: README says `src.main:app`, but `conftest.py` puts `src/` on `sys.path`, which implies `import main` style. These conflict if modules use `from src...` imports. | Use package-style `src/main.py` imported as `src.main`; add `src/__init__.py`; run pytest from the repo root. `conftest.py` will be adjusted if needed. |
| Q-9 | DB location for the running app? | `./src/tasks.db` (matches `.mcp.json`; `*.db` is already git-ignored). Tests use a separate temp/in-memory DB. |
| Q-10 | Delete response when the task exists: empty body with 204 (assumed). | Confirmed by story. |

## 9. Risks and Issues Found

| # | Severity | Item |
|---|----------|------|
| R-1 | HIGH (security) | `.env.example` contains what appears to be a real GitHub personal access token. `.gitignore` has `!.env.example`, so it would be committed and pushed in Stage 8. Recommend: revoke/rotate that token on GitHub now, replace the value with a placeholder, and keep real values only in the git-ignored `.env`. This workflow will not commit that file until it is sanitized. |
| R-2 | MEDIUM | Repo has no commits and no remote. Stage 8 (branch, push, PR) needs a configured GitHub remote and a base commit on `main`. The git status also shows the enclosing home directory (`C:\Users\ruchika_joshi`) is itself a git repo with `Capstone Claude` untracked inside it; the project folder should be its own repository. |
| R-3 | LOW | `README.md` contains stray shell text and should be cleaned during implementation. |
| R-4 | LOW | `requirements.txt` has unpinned `httpx`/`pytest` and duplicates `requirements-test.txt`. Acceptable; no change required by the story. |
| R-5 | INFO | sqlite MCP server failed to connect. Not needed for this story; tests use SQLAlchemy directly. |

## 10. Definition of Done
- All five endpoints implemented per FR-001..FR-008.
- Every Jira acceptance criterion has at least one passing automated test.
- `pytest` run output is reported as-is in `verification.md`.
- No secrets in the committed tree.
- PR opened against `main` after final human approval.

## 11. Approval
- [ ] Human approval of requirements and Q-1..Q-10 defaults (required before Stage 2)
