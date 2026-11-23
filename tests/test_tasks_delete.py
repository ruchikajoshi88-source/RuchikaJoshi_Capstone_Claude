def test_delete_existing_task_returns_204_with_empty_body(client, make_task):
    task = make_task()

    response = client.delete(f"/tasks/{task['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_deleted_task_is_gone_from_get_and_list(client, make_task):
    keep = make_task(title="keep")
    gone = make_task(title="gone")

    client.delete(f"/tasks/{gone['id']}")

    assert client.get(f"/tasks/{gone['id']}").status_code == 404
    assert client.get("/tasks").json() == [keep]


def test_delete_missing_task_returns_404_with_exact_detail(client):
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task with ID 999 does not exist"}


def test_delete_twice_returns_404_the_second_time(client, make_task):
    task = make_task()

    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.delete(f"/tasks/{task['id']}").status_code == 404


def test_ids_are_not_reused_after_deleting_the_newest_task(client, make_task):
    newest = make_task(title="newest")
    client.delete(f"/tasks/{newest['id']}")

    replacement = make_task(title="replacement")

    assert replacement["id"] > newest["id"]
