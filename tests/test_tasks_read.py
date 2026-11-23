def test_list_is_empty_array_when_no_tasks(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_all_tasks_ordered_by_id(client, make_task):
    created = [make_task(title=f"task {i}") for i in range(3)]

    response = client.get("/tasks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert [t["id"] for t in body] == sorted(t["id"] for t in created)
    assert body == created


def test_get_existing_task_returns_200(client, make_task):
    created = make_task(title="Read me", description="details", status="done")

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_task_returns_404_with_exact_detail(client):
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task with ID 999 does not exist"}
