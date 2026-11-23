import pytest


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"title": "t", "description": "d", "status": "blocked"}, id="invalid-status"),
        pytest.param({"title": "", "description": "d"}, id="empty-title"),
        pytest.param({"title": "   ", "description": "d"}, id="whitespace-only-title"),
        pytest.param({"title": "x" * 256, "description": "d"}, id="title-256-chars"),
        pytest.param({"description": "d"}, id="missing-title"),
        pytest.param({"title": "t"}, id="missing-description"),
        pytest.param({"title": 123, "description": "d"}, id="title-wrong-type"),
        pytest.param({}, id="empty-body"),
    ],
)
def test_create_rejects_invalid_payload_with_422(client, payload):
    response = client.post("/tasks", json=payload)

    assert response.status_code == 422
    assert client.get("/tasks").json() == []


def test_create_accepts_title_of_exactly_255_chars(client):
    response = client.post("/tasks", json={"title": "x" * 255, "description": "d"})

    assert response.status_code == 201
    assert len(response.json()["title"]) == 255


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"status": "blocked"}, id="invalid-status"),
        pytest.param({"title": ""}, id="empty-title"),
        pytest.param({"title": "   "}, id="whitespace-only-title"),
        pytest.param({"title": "x" * 256}, id="title-256-chars"),
        pytest.param({"title": None}, id="null-title"),
        pytest.param({"description": None}, id="null-description"),
        pytest.param({"status": None}, id="null-status"),
    ],
)
def test_patch_rejects_invalid_payload_with_422_and_changes_nothing(client, make_task, payload):
    task = make_task()

    response = client.patch(f"/tasks/{task['id']}", json=payload)

    assert response.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json() == task


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        pytest.param("get", {}, id="get"),
        pytest.param("patch", {"json": {"title": "x"}}, id="patch"),
        pytest.param("delete", {}, id="delete"),
    ],
)
def test_non_integer_task_id_returns_422(client, method, kwargs):
    response = getattr(client, method)("/tasks/abc", **kwargs)

    assert response.status_code == 422


@pytest.mark.parametrize("task_id", [2**63, -(2**63) - 1, 10**30])
@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        pytest.param("get", {}, id="get"),
        pytest.param("patch", {"json": {"title": "x"}}, id="patch"),
        pytest.param("delete", {}, id="delete"),
    ],
)
def test_task_id_beyond_sqlite_integer_range_returns_404_not_500(client, method, kwargs, task_id):
    response = getattr(client, method)(f"/tasks/{task_id}", **kwargs)

    assert response.status_code == 404
    assert response.json() == {"detail": f"Task with ID {task_id} does not exist"}


def test_patch_accepts_title_of_exactly_255_chars(client, make_task):
    task = make_task()

    response = client.patch(f"/tasks/{task['id']}", json={"title": "x" * 255})

    assert response.status_code == 200
    assert len(response.json()["title"]) == 255
