# SCRUM-7 — Architecture Design

- Stage: 2 of 8 (agent: solution-architect)
- Input: docs/plans/SCRUM-7/requirements.md (approved, defaults Q-1..Q-10 accepted)
- Environment observed: Python 3.13.14, FastAPI 0.165.0, Starlette 1.10.0, SQLAlchemy 2.1.9, Pydantic 2.14.4, pytest 9.2.0, httpx 0.28.1

## 1. Overview
A single-process FastAPI app exposing one resource (`/tasks`). Pydantic v2 models validate input and shape output. SQLAlchemy 2.x (typed `Mapped` style) persists to a SQLite file. Route handlers are plain `def` (sync) functions that receive a request-scoped `Session` through a FastAPI dependency; FastAPI runs them in its threadpool.

```
HTTP client
   |
   v
FastAPI app (src/main.py)  -- lifespan: create tables
   |
   v
Router (src/routers/tasks.py)  -- HTTP status codes, 404 mapping
   |        uses Pydantic schemas (src/schemas.py) for validation / response
   v
CRUD layer (src/crud.py)       -- queries only, no HTTP knowledge
   |
   v
SQLAlchemy Session (src/database.py: get_db) --> SQLite file (src/tasks.db)
                                  model: src/models.py (Task)
```

No extra services, queues, caches, auth, or migration tooling.

## 2. Module Layout

```
src/
  __init__.py        # makes `src` a package so `uvicorn src.main:app` works
  main.py            # FastAPI app, lifespan (create_all), include router
  database.py        # engine, SessionLocal, Base, get_db dependency
  models.py          # Task ORM model
  schemas.py         # TaskStatus enum, TaskCreate, TaskUpdate, TaskRead
  crud.py            # list/get/create/update/delete functions
  routers/
    __init__.py
    tasks.py         # APIRouter(prefix="/tasks")
tests/
  conftest.py        # in-memory DB engine, dependency override, client fixture
  test_tasks_create.py
  test_tasks_read.py
  test_tasks_update.py
  test_tasks_delete.py
  test_tasks_validation.py
```

Import style is package-absolute (`from src.database import ...`). `tests/` has no `__init__.py`, so pytest's `prepend` import mode would insert `tests/` (not the repo root) into `sys.path`. A new root `pytest.ini` sets `pythonpath = .` and `testpaths = tests`, so `src.*` resolves for a plain `pytest` run from the repo root (design review D-3). The existing root `conftest.py` puts `src/` on `sys.path`, which allows a second import identity (`main` vs `src.main`) and therefore two `Base`/engine copies; it is deleted (see ADR-5).

## 3. Data Model (`src/models.py`)

```python
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo")
```

- `status` is stored as a plain string per the story's data model; the allowed set is enforced at the API boundary by the Pydantic enum.
- `__table_args__ = {"sqlite_autoincrement": True}` makes SQLAlchemy emit SQLite `AUTOINCREMENT`, so IDs are never reused after deletes (design review D-1). A client holding a deleted task's ID can therefore never see it silently point at a different task.

## 4. API Contract (`src/schemas.py`, `src/routers/tasks.py`)

### Schemas
| Schema | Fields | Rules |
|--------|--------|-------|
| `TaskStatus` | `str` Enum: `todo`, `in_progress`, `done` | FR-007 |
| `TaskCreate` | `title: str`, `description: str`, `status: TaskStatus = todo` | `title` stripped, length 1..255 (whitespace-only rejected); `description` required, empty string allowed; `use_enum_values=True` |
| `TaskUpdate` | `title?`, `description?`, `status?` (all optional) | same per-field rules as create; explicit `null` on any field rejected via an after-validator over `model_fields_set`; `{}` allowed |
| `TaskRead` | `id`, `title`, `description`, `status` | `from_attributes=True`; no timestamps (Q-7) |

### Endpoints
| Method / Path | Handler behaviour | Success | Errors |
|---------------|-------------------|---------|--------|
| `POST /tasks` | create row, commit, refresh | `201` `TaskRead` | `422` invalid body |
| `GET /tasks` | all rows `ORDER BY id ASC` | `200` `list[TaskRead]` (`[]` when empty) | — |
| `GET /tasks/{task_id}` | get by PK | `200` `TaskRead` | `404`, `422` non-integer id |
| `PATCH /tasks/{task_id}` | `model_dump(exclude_unset=True)` applied to row, commit, refresh | `200` `TaskRead` | `404`, `422` |
| `DELETE /tasks/{task_id}` | delete row, commit | `204`, empty body | `404`, `422` |

Not-found is raised in the router as `HTTPException(404, detail=f"Task with ID {task_id} does not exist")`, producing `{"detail": "Task with ID 5 does not exist"}` (FR-008). Validation errors use FastAPI's default `422` body (Q-1). A private `_get_task_or_404` helper is shared by GET/PATCH/DELETE so the message exists in one place.

## 5. Persistence and Sessions (`src/database.py`)
- `DATABASE_URL` is a module constant: `sqlite:///<abs path of src/tasks.db>`, computed from `Path(__file__).parent` so it does not depend on the working directory. No environment-variable override (tests use a dependency override instead; design review D-2).
- Engine created with `connect_args={"check_same_thread": False}` because sync handlers execute in a threadpool.
- `SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)`.
- `get_db()` yields a session and closes it in `finally`.
- Tables are created in the FastAPI `lifespan` handler (`Base.metadata.create_all(bind=engine)`); `@app.on_event` is not used (deprecated).

## 6. Test Architecture (`tests/conftest.py`)
- Fixture builds a fresh in-memory SQLite engine per test: `create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)`, then `Base.metadata.create_all`.
- `app.dependency_overrides[get_db]` points at a session bound to that engine; cleared after each test.
- `TestClient(app)` is used **without** entering its context manager, so the production `lifespan` (which would create `src/tasks.db`) never runs during tests.
- Each test is independent: no shared state, no ordering dependence, no real DB file touched.
- Requirement coverage (AC-1..AC-6) is mapped in requirements.md section 5; validation cases cover invalid status, empty/whitespace/oversized title, `null` PATCH values, empty PATCH, non-integer id, missing `description`.

## 7. Architecture Decision Records

| ADR | Decision | Reason | Alternative rejected |
|-----|----------|--------|----------------------|
| 1 | Sync handlers + sync SQLAlchemy | Simplest correct option with SQLite; no async driver dependency | `aiosqlite` + async engine: extra dependency, no benefit at this scale |
| 2 | Separate `crud.py` | Keeps router free of query code and makes the 404 mapping the router's only concern | Queries inline in router: smaller but mixes concerns |
| 3 | Enum enforced in Pydantic only; DB column is plain `String(20)` | Matches story's data model exactly | DB `CHECK` constraint / SQL Enum: extra schema surface not requested |
| 4 | `create_all` on startup, no Alembic | Single table, no migration requirement in the story | Alembic: out of scope |
| 5 | Package-style imports (`src.*`); delete root `conftest.py`, add `pytest.ini` with `pythonpath = .` | README run command is `uvicorn src.main:app`; avoids double module identity; works for plain `pytest` | Keep `sys.path` insert and import `main`: breaks README command |
| 6 | Tests use in-memory SQLite via dependency override | Isolation and speed; never touches `src/tasks.db` | Temp file DB: slower, cleanup needed |
| 7 | `PATCH` via `exclude_unset` + reject explicit `null` | Gives true partial-update semantics (AC-4) while protecting NOT NULL columns | Treat `null` as "no change": hides client mistakes |

## 8. Risks / Notes
| ID | Note |
|----|------|
| A-R1 | SQLAlchemy 2.1 and Starlette 1.x are newer than the `>=` floors in `requirements.txt`. Code uses only stable 2.0-style APIs (`Mapped`, `select`, `Session.get`). Pinning exact versions is recommended but not required by the story. |
| A-R2 | Resolved by review D-1: `sqlite_autoincrement=True` so IDs are not reused after delete. A test asserts that a new task after deleting the newest one gets a higher ID. |
| A-R3 | No concurrency control (last write wins on concurrent PATCH). Out of scope for a single-user story. |
| A-R4 | Untrusted input is limited to JSON bodies and an integer path param; all DB access uses ORM parameter binding (no string-built SQL). |

## 9. Traceability
| Requirement | Design element |
|-------------|----------------|
| FR-001, AC-1 | `POST /tasks`, `TaskCreate`, `TaskRead` |
| FR-002, AC-2 | `GET /tasks`, `crud.list_tasks` |
| FR-003, AC-3 | `GET /tasks/{id}`, `_get_task_or_404` |
| FR-004, AC-4 | `PATCH /tasks/{id}`, `TaskUpdate` |
| FR-005, AC-5 | `DELETE /tasks/{id}` status 204 |
| FR-006 | `Task.id` PK autoincrement |
| FR-007 | `TaskStatus` enum + default `todo` |
| FR-008 | 404 `HTTPException` message |
| AC-6 | `tests/` package, in-memory DB fixture |
