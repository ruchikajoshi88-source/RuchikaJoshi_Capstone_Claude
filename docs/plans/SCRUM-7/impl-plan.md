# SCRUM-7 — Implementation Plan

- Stage: 4 of 8 (agent: branch-git-planner)
- Inputs: requirements.md (approved), architecture.md, design-review.md (D-1..D-3 applied)
- Status: DRAFT — awaiting human approval (gate 2 of 3)

## 1. Branch and Git Plan

### Observed git state
- `git rev-parse --show-toplevel` returns `C:/Users/ruchika_joshi` (home directory), not the project folder. `Capstone Claude/` is untracked inside that repo.
- Branch `main` has no commits; no remotes.
- `.gitignore` already excludes `.venv/`, `.env`, `.env.*` (except `.env.example`), `*.db`, `.cache/`, `.claude/settings.local.json`, `.pytest_cache/`.
- `docs/codemie/analytics/*.json` are CodeMie usage exports with the user's work email in the filename; unrelated to the story.

### Plan
| Step | Action | Notes |
|------|--------|-------|
| G-0 | `git init -b main` inside `Capstone Claude/` so the project is its own repository | Creates a nested repo; home-directory repo is untouched (it only sees an untracked folder). Needs approval, see section 6. |
| G-1 | Base commit on `main`: scaffolding + SDLC artifacts for stages 1-4 | Stage explicitly by path (never `git add -A`). Includes `CLAUDE.md`, `.claude/` (agents, commands, rules, hooks, `settings.json`), `.github/`, `.gitignore`, `.mcp.json`, `README.md`, `requirements*.txt`, `context/`, `docs/plans/SCRUM-7/`, sanitized `.env.example`. Excludes `.env`, `.venv/`, `.cache/`, `docs/codemie/`, `.claude/settings.local.json`. |
| G-2 | Create branch `feature/SCRUM-7-task-management-api` from `main` | Naming: `feature/<JIRA-KEY>-<slug>`. |
| G-3 | Implementation commits on the feature branch (table in section 3) | Commit subject prefix `SCRUM-7:`; trailer `Co-Authored-By: Claude Code <noreply@anthropic.com>`. No `--no-verify`. |
| G-4 | Stage 8: add remote, push branch, open PR to `main` with `.github/PULL_REQUEST_TEMPLATE.md` | Only after final human approval and token hygiene (R-1). |

## 2. Pre-flight Gate (blocks G-1)
| ID | Task | Owner |
|----|------|-------|
| P-1 | Revoke/rotate the GitHub token that is in `.env.example` | **User** (cannot be done by the workflow) |
| P-2 | Replace token value in `.env.example` with `GITHUB_TOKEN=` (empty placeholder). Keep the other three keys. | Developer agent |
| P-3 | Grep the to-be-committed tree for `github_pat_`, `ghp_`, `API_TOKEN=` with a value, `.env` content; must return nothing | Developer agent |

## 3. Task Breakdown

| # | Task | Files | Depends on | Commit |
|---|------|-------|-----------|--------|
| T-1 | Test/runtime config: add `pytest.ini` (`pythonpath = .`, `testpaths = tests`); delete root `conftest.py`; add `src/__init__.py`, `src/routers/__init__.py` | `pytest.ini`, `conftest.py` (delete), `src/__init__.py`, `src/routers/__init__.py` | G-2 | `SCRUM-7: add package layout and pytest config` |
| T-2 | Database + model: `Base`, engine (`check_same_thread=False`), `SessionLocal`, `get_db`; `Task` model with `sqlite_autoincrement=True` | `src/database.py`, `src/models.py` | T-1 | `SCRUM-7: add database setup and Task model` |
| T-3 | Schemas: `TaskStatus`, `TaskCreate`, `TaskUpdate` (reject explicit null), `TaskRead` | `src/schemas.py` | T-1 | `SCRUM-7: add Pydantic schemas` |
| T-4 | CRUD functions + router + app: five endpoints, shared 404 helper with exact message, lifespan `create_all` | `src/crud.py`, `src/routers/tasks.py`, `src/main.py` | T-2, T-3 | `SCRUM-7: add task CRUD endpoints` |
| T-5 | Tests: `tests/conftest.py` fixtures + test modules (section 4) | `tests/conftest.py`, `tests/test_tasks_*.py` | T-4 | `SCRUM-7: add pytest suite for task API` |
| T-6 | Docs: replace `README.md` with clean run/test/endpoint instructions (remove stray `Set-Content...` text) | `README.md` | T-4 | `SCRUM-7: update README` |

T-5 may be written test-first against the schemas/router signatures; either order is acceptable as long as the suite is run for real before Stage 7 sign-off.

Implementation rules for the developer agent:
- Only files in the table above (plus the artifacts under `docs/plans/SCRUM-7/`). No extra frameworks, no auth, no timestamps, no pagination.
- Sync SQLAlchemy 2.x style (`Mapped`, `select`, `Session.get`); Pydantic v2 APIs only (`model_dump`, `ConfigDict`, `StringConstraints`).
- Title: `StringConstraints(strip_whitespace=True, min_length=1, max_length=255)`.
- Handlers declare `status_code` explicitly (201, 200, 204).
- No comments except where a constraint is non-obvious.

## 4. Test Plan (pytest, in-memory SQLite, `TestClient` without lifespan)

| Module | Cases | Covers |
|--------|-------|--------|
| `test_tasks_create.py` | create returns 201 + `id` + echoed fields; status defaults to `todo`; explicit status accepted for each of 3 values; second task gets larger `id`; `description` empty string accepted; title surrounding whitespace is stripped | AC-1, FR-001, FR-006, FR-007 |
| `test_tasks_read.py` | list empty -> `200 []`; list after 3 creates returns 3 ordered by id; get existing -> 200 and matching body; get missing -> 404 with exact `{"detail": "Task with ID 999 does not exist"}` | AC-2, AC-3, FR-002, FR-003, FR-008 |
| `test_tasks_update.py` | patch title only leaves description/status unchanged; patch status only; patch all three; `{}` -> 200 unchanged; patch missing -> 404 exact message; change persists on subsequent GET | AC-4, FR-004, FR-008 |
| `test_tasks_delete.py` | delete existing -> 204 and empty body; subsequent GET -> 404; list no longer contains it; delete missing -> 404 exact message; new task after deleting the newest gets a higher id (no reuse) | AC-5, FR-005, FR-008, D-1, D-7 |
| `test_tasks_validation.py` | create: invalid status, empty title, whitespace-only title, title of 256 chars (and 255 accepted), missing title, missing description -> 422; patch: invalid status, `null` title/description/status, empty title -> 422; `/tasks/abc` on GET/PATCH/DELETE -> 422 | Q-1, Q-2, Q-3, Q-4, Q-6, D-6 |

Expected total: about 35 test functions (parametrized). All must be genuinely executed; reported numbers come from the real pytest output.

## 5. Quality Gates per Stage
| Gate | Check |
|------|-------|
| Before commit | `git status` reviewed; staged files listed by path; secret grep (P-3) clean; `.env` and `*.db` not staged |
| Stage 5 exit | App imports (`python -c "import src.main"`), `pytest` runs |
| Stage 6 | Code review against architecture + requirements; findings fixed or recorded |
| Stage 7 | `pytest -v` full output captured in `verification.md`; AC-1..AC-6 each mapped to passing tests; manual smoke run of `uvicorn src.main:app` hitting each endpoint if feasible |
| Stage 8 | Final human approval; PR body from template; audit report `docs/workflow-report-WF-2026-001.html` generated |

## 6. Decisions Needed From You at This Gate
1. **Own repository (G-0):** OK to run `git init -b main` inside `Capstone Claude/`? (Recommended. The alternative is committing into the home-directory repo, which would be exposed to all of your profile folders and is not recommended.)
2. **Remote (G-4):** the GitHub `owner/repo` to push to and open the PR in. Does the repository already exist, or should the workflow create it (via the GitHub MCP)? Visibility (private recommended)?
3. **Token (P-1):** confirm you will rotate the token found in `.env.example`; the workflow will blank it in the file but cannot revoke it.
4. **Exclusions:** confirm `docs/codemie/` (analytics exports) stays out of the commit.
5. Anything in the plan to change (branch name, commit granularity, test list)?

## 7. Approval
- [ ] Human approval of implementation plan (required before Stage 5 Development)
