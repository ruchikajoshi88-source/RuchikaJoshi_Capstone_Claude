def test_patch_title_only_leaves_other_fields_unchanged(client, make_task):
    task = make_task(title="old", description="keep", status="in_progress")

    response = client.patch(f"/tasks/{task['id']}", json={"title": "new"})

    assert response.status_code == 200
    assert response.json() == {**task, "title": "new"}


def test_patch_status_only_leaves_other_fields_unchanged(client, make_task):
    task = make_task(title="t", description="d")

    response = client.patch(f"/tasks/{task['id']}", json={"status": "done"})

    assert response.status_code == 200
    assert response.json() == {**task, "status": "done"}


def test_patch_description_only_leaves_other_fields_unchanged(client, make_task):
    task = make_task(title="t", description="d")

    response = client.patch(f"/tasks/{task['id']}", json={"description": "changed"})

    assert response.status_code == 200
    assert response.json() == {**task, "description": "changed"}


def test_patch_all_fields(client, make_task):
    task = make_task()

    payload = {"title": "T2", "description": "D2", "status": "done"}
    response = client.patch(f"/tasks/{task['id']}", json=payload)

    assert response.status_code == 200
    assert response.json() == {"id": task["id"], **payload}


def test_patch_empty_body_returns_task_unchanged(client, make_task):
    task = make_task()

    response = client.patch(f"/tasks/{task['id']}", json={})

    assert response.status_code == 200
    assert response.json() == task


def test_patch_missing_task_returns_404_with_exact_detail(client):
    response = client.patch("/tasks/999", json={"title": "x"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task with ID 999 does not exist"}


def test_patch_change_persists_on_subsequent_get(client, make_task):
    task = make_task(title="before")

    client.patch(f"/tasks/{task['id']}", json={"title": "after"})
    response = client.get(f"/tasks/{task['id']}")

    assert response.json()["title"] == "after"
