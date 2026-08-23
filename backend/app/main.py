from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models import ErrorResponse, TaskInput, TaskResponse, TaskUpdate
from .repository import PostgresTaskRepository, TaskRepository


def _as_response(task: object) -> TaskResponse:
    return TaskResponse.model_validate(task, from_attributes=True)


def _not_found() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Task not found"})


def create_app(repository: TaskRepository | None = None) -> FastAPI:
    """Create an app that can be supplied an isolated repository in tests."""

    task_repository = repository or PostgresTaskRepository(
        os.environ.get("DATABASE_URL", "")
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task_repository.initialize()
        yield

    app = FastAPI(
        title="FlyRank Backend Assignment 3",
        version="1.0.0",
        description="Containerized FastAPI and PostgreSQL task API.",
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid request: {exc.errors()[0]['msg']}"},
        )

    @app.get("/health", response_model=dict[str, str])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/tasks", response_model=list[TaskResponse])
    def list_tasks() -> list[TaskResponse]:
        return [_as_response(task) for task in task_repository.list_tasks()]

    @app.post(
        "/tasks",
        response_model=TaskResponse,
        status_code=status.HTTP_201_CREATED,
        responses={400: {"model": ErrorResponse}},
    )
    def create_task(payload: TaskInput) -> TaskResponse:
        task = task_repository.create_task(
            payload.title, payload.description, payload.completed
        )
        return _as_response(task)

    @app.get(
        "/tasks/{task_id}",
        response_model=TaskResponse,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def get_task(task_id: int) -> TaskResponse | JSONResponse:
        task = task_repository.get_task(task_id)
        if task is None:
            return _not_found()
        return _as_response(task)

    @app.put(
        "/tasks/{task_id}",
        response_model=TaskResponse,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def update_task(task_id: int, payload: TaskUpdate) -> TaskResponse | JSONResponse:
        task = task_repository.update_task(
            task_id, payload.model_dump(exclude_unset=True)
        )
        if task is None:
            return _not_found()
        return _as_response(task)

    @app.delete(
        "/tasks/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        response_model=None,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def delete_task(task_id: int) -> Response | JSONResponse:
        if not task_repository.delete_task(task_id):
            return _not_found()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()