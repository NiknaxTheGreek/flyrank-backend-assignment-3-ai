from fastapi.testclient import TestClient

from backend.app.repository import InMemoryTaskRepository


def test_assignment_2_root_and_health_compatibility(client: TestClient) -> None:
    assert client.get("/").json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }
    assert client.get("/health").json() == {"status": "ok"}


def test_assignment_2_crud_lifecycle_and_shape(client: TestClient) -> None:
    assert client.get("/tasks").json() == [
        {"id": 1, "title": "Learn FastAPI", "done": False},
        {"id": 2, "title": "Build a CRUD API", "done": False},
        {"id": 3, "title": "Read the assignment", "done": True},
    ]

    created = client.post("/tasks", json={"title": "Ship Assignment 3"})
    assert created.status_code == 201
    task = created.json()
    assert task == {"id": 4, "title": "Ship Assignment 3", "done": False}
    assert client.get("/tasks/4").json() == task

    updated = client.put("/tasks/4", json={"done": True})
    assert updated.status_code == 200
    assert updated.json() == {**task, "done": True}

    deleted = client.delete("/tasks/4")
    assert deleted.status_code == 204
    assert deleted.content == b""


def test_assignment_2_validation_and_path_errors(client: TestClient) -> None:
    invalid_requests = (
        ("post", "/tasks", {}),
        ("post", "/tasks", {"title": "   "}),
        ("post", "/tasks", {"title": "Do not accept done", "done": True}),
        ("post", "/tasks", {"title": "Wrong type", "done": "true"}),
        ("get", "/tasks/not-an-id", None),
    )
    for method, path, payload in invalid_requests:
        response = (
            getattr(client, method)(path, json=payload)
            if payload is not None
            else getattr(client, method)(path)
        )
        assert response.status_code == 400
        assert response.json() == {"error": "Invalid request body"}

    empty_update = client.put("/tasks/1", json={})
    assert empty_update.status_code == 400
    assert empty_update.json() == {
        "error": "Request body must include title and/or done"
    }

    for task_id in (0, -1, 9999):
        for method, payload in (
            ("get", None),
            ("put", {"done": True}),
            ("delete", None),
        ):
            response = (
                getattr(client, method)(f"/tasks/{task_id}", json=payload)
                if payload is not None
                else getattr(client, method)(f"/tasks/{task_id}")
            )
            assert response.status_code == 404
            assert response.json() == {"error": f"Task {task_id} not found"}


def test_assignment_2_nullable_and_partial_update_compatibility(
    client: TestClient,
) -> None:
    nullable_title = client.put("/tasks/1", json={"title": None})
    assert nullable_title.status_code == 200
    assert nullable_title.json() == {"id": 1, "title": None, "done": False}

    nullable_done = client.put("/tasks/1", json={"done": None})
    assert nullable_done.status_code == 200
    assert nullable_done.json() == {"id": 1, "title": None, "done": None}

    coercible_done = client.put("/tasks/2", json={"done": "true"})
    assert coercible_done.status_code == 200
    assert coercible_done.json() == {
        "id": 2,
        "title": "Build a CRUD API",
        "done": True,
    }


def test_hostile_sql_looking_text_is_stored_as_task_data(client: TestClient) -> None:
    hostile_title = "'); DROP TABLE tasks; --"

    created = client.post("/tasks", json={"title": hostile_title})

    assert created.status_code == 201
    assert created.json()["title"] == hostile_title
    assert any(task["title"] == hostile_title for task in client.get("/tasks").json())


def test_seeding_does_not_duplicate_when_initialized_again(
    repository: InMemoryTaskRepository,
) -> None:
    repository.initialize()
    repository.initialize()

    assert len(repository.list_tasks()) == 3