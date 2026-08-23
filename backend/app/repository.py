from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class Task:
    id: int
    title: str | None
    done: bool | None


STARTER_TASKS: tuple[tuple[str, bool], ...] = (
    ("Learn FastAPI", False),
    ("Build a CRUD API", False),
    ("Read the assignment", True),
)


class TaskRepository(Protocol):
    def initialize(self) -> None: ...

    def list_tasks(self) -> list[Task]: ...

    def get_task(self, task_id: int) -> Task | None: ...

    def create_task(self, title: str, done: bool) -> Task: ...

    def update_task(
        self, task_id: int, title: str | None, done: bool | None, fields: set[str]
    ) -> Task | None: ...

    def delete_task(self, task_id: int) -> bool: ...


def _task_from_row(row: dict[str, Any]) -> Task:
    return Task(
        id=int(row["id"]),
        title=row["title"],
        done=row["done"],
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
                    title VARCHAR(200),
                    done BOOLEAN
                )
                """
            )
            cursor.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS done BOOLEAN")
            cursor.execute("ALTER TABLE tasks ALTER COLUMN title DROP NOT NULL")
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'tasks' AND column_name = 'completed'
                    ) THEN
                        EXECUTE 'UPDATE tasks SET done = completed WHERE done IS NULL';
                    END IF;
                END
                $$
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
                    INSERT INTO tasks (title, done)
                    VALUES (%s, %s)
                    """,
                    STARTER_TASKS,
                )

    def list_tasks(self) -> list[Task]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, done
                FROM tasks
                ORDER BY id
                """
            )
            return [_task_from_row(row) for row in cursor.fetchall()]

    def get_task(self, task_id: int) -> Task | None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, done
                FROM tasks
                WHERE id = %s
                """,
                (task_id,),
            )
            row = cursor.fetchone()
            return _task_from_row(row) if row else None

    def create_task(self, title: str, done: bool) -> Task:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done
                """,
                (title, done),
            )
            return _task_from_row(cursor.fetchone())

    def update_task(
        self, task_id: int, title: str | None, done: bool | None, fields: set[str]
    ) -> Task | None:
        if not fields or not fields.issubset({"title", "done"}):
            raise ValueError("invalid task update")

        assignments: list[str] = []
        values: list[str | bool | None] = []
        if "title" in fields:
            assignments.append("title = %s")
            values.append(title)
        if "done" in fields:
            assignments.append("done = %s")
            values.append(done)
        values.append(task_id)
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tasks
                SET {", ".join(assignments)}
                WHERE id = %s
                RETURNING id, title, done
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
        for title, done in STARTER_TASKS:
            self.create_task(title, done)

    def list_tasks(self) -> list[Task]:
        return [self._tasks[task_id] for task_id in sorted(self._tasks)]

    def get_task(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def create_task(self, title: str, done: bool) -> Task:
        task = Task(
            id=self._next_id,
            title=title,
            done=done,
        )
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def update_task(
        self, task_id: int, title: str | None, done: bool | None, fields: set[str]
    ) -> Task | None:
        existing = self._tasks.get(task_id)
        if not existing:
            return None
        task = Task(
            id=existing.id,
            title=title if "title" in fields else existing.title,
            done=done if "done" in fields else existing.done,
        )
        self._tasks[task_id] = task
        return task

    def delete_task(self, task_id: int) -> bool:
        return self._tasks.pop(task_id, None) is not None