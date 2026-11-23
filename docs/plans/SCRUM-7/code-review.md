# SCRUM-7 — Code Review

- Stage: 6 of 8 (agent: code-reviewer)
- Scope: `git diff main...feature/SCRUM-7-task-management-api` (src/, tests/, README, pytest.ini, config)
- Method: (a) author self-review with edge-case probing, (b) independent review by a separate fresh-context agent that ran read-only on commit cc7c19c and probed behaviour in memory
- Verdict: **APPROVED WITH CHANGES** — the one required change (CR-1) is fixed and tested

## 1. Findings

| ID | Severity | Status | Finding | Resolution |
|----|----------|--------|---------|------------|
| CR-1 | Medium (bug, FR-008) | **FIXED** (commit "return 404 for task IDs outside SQLite integer range") | `GET`/`PATCH`/`DELETE /tasks/{id}` with an ID outside the signed 64-bit range (e.g. `99999999999999999999`, `2**63`) raised `OverflowError` inside SQLite binding and returned **500** instead of 404. Found independently by both reviewers. | `crud.get_task` returns `None` for out-of-range IDs so the router emits the standard 404 message. 9 new parametrized tests (3 ids x 3 methods). Mutation check: with the fix reverted, exactly those 9 tests fail; with it, all pass. |
| CR-2 | Low | Accepted | No DB `CHECK` on `status` and no length cap on `description` (a 100,000-char description is accepted). | Out of story scope; Pydantic enum guards status at the API boundary (ADR-3). Not changed. |
| CR-3 | Low | Accepted | Title containing a NUL character is accepted; unknown request fields (e.g. `PATCH {"id": 99}`) are silently ignored (no `extra="forbid"`). | Not required by story; behaviour is safe (id cannot be overwritten). Recorded for the team. |
| CR-4 | Low | Partly addressed | Test gaps: production `lifespan`/`create_all` path is not exercised by pytest (deliberate, to avoid creating `src/tasks.db`); no PATCH 255-char boundary test. | PATCH 255-char test added. Lifespan/startup is covered by a manual `uvicorn` smoke test in Stage 7 (verification.md). |
| CR-5 | Info | Open (not in diff) | `.env.example` names `CAPSTONE_JIRA_USERNAME` / `CAPSTONE_JIRA_API_TOKEN` but `.mcp.json` reads `${JIRA_USERNAME}` / `${JIRA_API_TOKEN}`, so values copied from the example will not reach the Jira MCP server. | Pre-existing config, outside the story; flagged for the owner. |
| CR-6 | Info | Open | `StarletteDeprecationWarning` about `httpx` in `starlette.testclient` (installed Starlette 1.10 prefers `httpx2`). | Non-failing; dependency choice left as-is per scope. |

## 2. Verified Correct (by reviewers, with behaviour probes)
- 201 on create with generated `id`; status defaults to `todo`; `status: null` rejected (422).
- Title stripped before length check: padded 255-char title accepted, 256 chars and whitespace-only rejected.
- PATCH uses `exclude_unset`: `{}` returns 200 unchanged; explicit `null` returns 422; unknown ID returns 404 with exact message.
- DELETE returns 204 with an empty body; list is ordered by `id`; IDs are not reused after deleting the newest task (`sqlite_autoincrement`, DDL verified to contain `AUTOINCREMENT`).
- Non-integer ID returns 422; invalid JSON returns 422; `PUT` returns 405 (not implemented, out of scope).
- Tests are isolated (in-memory SQLite + dependency override); no test creates `src/tasks.db`; no vacuous assertions found.

## 3. Scope and Security
- Scope: only CRUD on `/tasks` plus supporting files. No extra frameworks, auth, timestamps, pagination. FR-001..FR-008 all implemented.
- Secrets: `.env.example` contains only blank placeholders; the real token never entered git history (blanked before the first commit). `.mcp.json` uses `${VAR}` references only. `docs/codemie/` is git-ignored. R-1 remains an action for the user: the token that was in the file must be revoked/rotated.
- All DB access uses ORM parameter binding; no raw SQL.

## 4. Review Limitations
- The author performed the first review pass; the independent pass reduces but does not remove same-model bias. Neither pass is a substitute for human review at the PR gate.

## 5. Outcome
Proceed to Stage 7 (Verification). Suite after fixes (real run): 53 passed, 1 warning.
