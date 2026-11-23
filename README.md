# Task Management REST API

A small CRUD API for tasks built with FastAPI, SQLAlchemy, SQLite and Pydantic v2 (Jira story SCRUM-7).

## Setup

```
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
```

## Run

```
uvicorn src.main:app --reload
```

The SQLite file is created at `src/tasks.db` on first start. Interactive docs are at http://127.0.0.1:8000/docs.

## Test

```
pytest
```

Tests use an in-memory database and never touch `src/tasks.db`.

## Endpoints

| Method | Path | Success | Notes |
|--------|------|---------|-------|
| POST | `/tasks` | 201 | Body: `title` (1-255 chars), `description`, optional `status` (default `todo`) |
| GET | `/tasks` | 200 | Array of tasks ordered by `id` |
| GET | `/tasks/{id}` | 200 | |
| PATCH | `/tasks/{id}` | 200 | Any subset of `title`, `description`, `status`; `null` is rejected |
| DELETE | `/tasks/{id}` | 204 | Empty body |

`status` is one of `todo`, `in_progress`, `done`. Invalid input returns 422. An unknown id returns 404 with `{"detail": "Task with ID {id} does not exist"}`.

## Configuration

Copy `.env.example` to `.env` for the SDLC tooling (GitHub / Jira credentials). The API itself needs no environment variables. Never commit `.env`.
