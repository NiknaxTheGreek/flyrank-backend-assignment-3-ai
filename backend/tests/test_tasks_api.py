from fastapi.testclient import TestClient

from backend.app.repository import InMemoryTaskRepository


def test_starts_with_exactly_three_tasks(client: TestClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_full_crud_lifecycle(client: TestClient) -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Ship assignment",
            "description": "Package FastAPI with PostgreSQL.",
            "completed": False,
        },
    )

    assert created.status_code == 201
    task = created.json()
    assert task["id"] == 4

    fetched = client.get(f"/tasks/{task['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == task

    updated = client.put(f"/tasks/{task['id']}", json={"completed": True})
    assert updated.status_code == 200
    assert updated.json() == {**task, "completed": True}

    deleted = client.delete(f"/tasks/{task['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""


def test_partial_put_preserves_unspecified_fields(client: TestClient) -> None:
    created = client.post(
        "/tasks",
        json={"title": "Keep my description", "description": "Do not overwrite me."},
    ).json()

    updated = client.put(f"/tasks/{created['id']}", json={"title": "Renamed"})

    assert updated.status_code == 200
    assert updated.json()["title"] == "Renamed"
    assert updated.json()["description"] == "Do not overwrite me."
    assert updated.json()["completed"] is False


def test_validation_returns_400_not_framework_default(client: TestClient) -> None:
    invalid_payloads = [
        {},
        {"title": "   "},
        {"title": "valid", "unknown": "field"},
    ]

    for payload in invalid_payloads:
        response = client.post("/tasks", json=payload)
        assert response.status_code == 400
        assert "error" in response.json()

    assert client.put("/tasks/1", json={}).status_code == 400
    assert client.put("/tasks/1", json={"title": None}).status_code == 400
    assert client.get("/tasks/not-a-number").status_code == 400


def test_missing_ids_return_404(client: TestClient) -> None:
    responses = (
        client.get("/tasks/99999"),
        client.put("/tasks/99999", json={"completed": True}),
        client.delete("/tasks/99999"),
    )
    assert all(response.status_code == 404 for response in responses)
    assert all(response.json() == {"error": "Task not found"} for response in responses)


def test_hostile_sql_looking_text_is_stored_as_task_data(client: TestClient) -> None:
    hostile_title = "'); DROP TABLE tasks; --"

    created = client.post("/tasks", json={"title": hostile_title})

    assert created.status_code == 201
    assert created.json()["title"] == hostile_title
    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert any(task["title"] == hostile_title for task in listed.json())


def test_seeding_does_not_duplicate_when_initialized_again(
    repository: InMemoryTaskRepository,
) -> None:
    repository.initialize()
    repository.initialize()

    assert len(repository.list_tasks()) == 3