from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    description: str
    completed: bool


STARTER_TASKS: tuple[tuple[str, str, bool], ...] = (
    ("Review the assignment", "Read the FastAPI and PostgreSQL requirements.", False),
    ("Start the API", "Run docker compose up --build.", False),
    ("Verify persistence", "Restart the compose stack without removing volumes.", False),
)


class TaskRepository(Protocol):
    def initialize(self) -> None: ...

    def list_tasks(self) -> list[Task]: ...

    def get_task(self, task_id: int) -> Task | None: ...

    def create_task(self, title: str, description: str, completed: bool) -> Task: ...

    def update_task(self, task_id: int, changes: dict[str, Any]) -> Task | None: ...

    def delete_task(self, task_id: int) -> bool: ...


def _task_from_row(row: dict[str, Any]) -> Task:
    return Task(
        id=int(row["id"]),
        title=str(row["title"]),
        description=str(row["description"]),
        completed=bool(row["completed"]),
    )


class PostgresTaskRepository:
    """Small parameterized-SQL repository used by the Dockerized application."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    @contextmanager
    def _connection(self) -> Iterable[psycopg.Connection[dict[str, Any]]]:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL must be set")
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            yield connection

    def initialize(self) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id BIGSERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    description VARCHAR(2000) NOT NULL DEFAULT '',
                    completed BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            # A transaction-level table lock avoids duplicate starter rows if two
            # API instances start at the same time against a fresh database.
            cursor.execute("LOCK TABLE tasks IN SHARE ROW EXCLUSIVE MODE")
            cursor.execute("SELECT COUNT(*) AS task_count FROM tasks")
            row = cursor.fetchone()
            if row and row["task_count"] == 0:
                cursor.executemany(
                    """
                    INSERT INTO tasks (title, description, completed)
                    VALUES (%s, %s, %s)
                    """,
                    STARTER_TASKS,
                )

    def list_tasks(self) -> list[Task]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, description, completed
                FROM tasks
                ORDER BY id
                """
            )
            return [_task_from_row(row) for row in cursor.fetchall()]

    def get_task(self, task_id: int) -> Task | None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, description, completed
                FROM tasks
                WHERE id = %s
                """,
                (task_id,),
            )
            row = cursor.fetchone()
            return _task_from_row(row) if row else None

    def create_task(self, title: str, description: str, completed: bool) -> Task:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, description, completed)
                VALUES (%s, %s, %s)
                RETURNING id, title, description, completed
                """,
                (title, description, completed),
            )
            return _task_from_row(cursor.fetchone())

    def update_task(self, task_id: int, changes: dict[str, Any]) -> Task | None:
        allowed_fields = {"title", "description", "completed"}
        if not changes or not set(changes).issubset(allowed_fields):
            raise ValueError("invalid task update")

        assignments = ", ".join(f"{field_name} = %s" for field_name in changes)
        values = [changes[field_name] for field_name in changes]
        values.append(task_id)
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tasks
                SET {assignments}
                WHERE id = %s
                RETURNING id, title, description, completed
                """,
                values,
            )
            row = cursor.fetchone()
            return _task_from_row(row) if row else None

    def delete_task(self, task_id: int) -> bool:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
            return cursor.fetchone() is not None


class InMemoryTaskRepository:
    """Deterministic repository used only by the HTTP regression suite."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def initialize(self) -> None:
        if self._tasks:
            return
        for title, description, completed in STARTER_TASKS:
            self.create_task(title, description, completed)

    def list_tasks(self) -> list[Task]:
        return [self._tasks[task_id] for task_id in sorted(self._tasks)]

    def get_task(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def create_task(self, title: str, description: str, completed: bool) -> Task:
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            completed=completed,
        )
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def update_task(self, task_id: int, changes: dict[str, Any]) -> Task | None:
        existing = self._tasks.get(task_id)
        if not existing:
            return None
        task = Task(
            id=existing.id,
            title=changes.get("title", existing.title),
            description=changes.get("description", existing.description),
            completed=changes.get("completed", existing.completed),
        )
        self._tasks[task_id] = task
        return task

    def delete_task(self, task_id: int) -> bool:
        return self._tasks.pop(task_id, None) is not None