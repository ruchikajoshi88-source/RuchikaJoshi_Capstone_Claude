import pytest


def test_create_returns_201_with_generated_id(client):
    response = client.post(
        "/tasks",
        json={"title": "Buy milk", "description": "2 litres", "status": "in_progress"},
    )

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["title"] == "Buy milk"
    assert body["description"] == "2 litres"
    assert body["status"] == "in_progress"


def test_create_defaults_status_to_todo(client):
    response = client.post("/tasks", json={"title": "Plan", "description": "week"})

    assert response.status_code == 201
    assert response.json()["status"] == "todo"


@pytest.mark.parametrize("status", ["todo", "in_progress", "done"])
def test_create_accepts_each_allowed_status(client, status):
    response = client.post(
        "/tasks", json={"title": "t", "description": "d", "status": status}
    )

    assert response.status_code == 201
    assert response.json()["status"] == status


def test_create_assigns_increasing_ids(client, make_task):
    first = make_task(title="one")
    second = make_task(title="two")

    assert second["id"] > first["id"]


def test_create_accepts_empty_description(client):
    response = client.post("/tasks", json={"title": "t", "description": ""})

    assert response.status_code == 201
    assert response.json()["description"] == ""


def test_create_strips_surrounding_whitespace_from_title(client):
    response = client.post("/tasks", json={"title": "  padded  ", "description": "d"})

    assert response.status_code == 201
    assert response.json()["title"] == "padded"
