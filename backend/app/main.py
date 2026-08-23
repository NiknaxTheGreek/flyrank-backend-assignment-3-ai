from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models import Task, TaskCreate, TaskUpdate
from .repository import PostgresTaskRepository, TaskRepository


def create_app(repository: TaskRepository | None = None) -> FastAPI:
    task_repository = repository or PostgresTaskRepository(
        os.environ.get("DATABASE_URL", "")
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task_repository.initialize()
        yield

    app = FastAPI(
        title="FlyRank Backend Assignment 2",
        version="1.0.0",
        description="SQLite-backed persistence for the Assignment 1 task CRUD API.",
        lifespan=lifespan,
    )
    app.state.repository = task_repository

    @app.exception_handler(RequestValidationError)
    async def invalid_request(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"error": "Invalid request body"}),
        )

    def get_repository(request: Request) -> TaskRepository:
        return request.app.state.repository

    @app.get("/", status_code=status.HTTP_200_OK)
    def api_information() -> dict[str, str | list[str]]:
        return {
            "name": "Task API",
            "version": "1.0",
            "endpoints": ["/tasks"],
        }

    @app.get("/health", status_code=status.HTTP_200_OK)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/tasks", response_model=list[Task], status_code=status.HTTP_200_OK)
    def list_tasks(request: Request) -> list[Task]:
        return get_repository(request).list_tasks()

    @app.get("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
    def get_task(request: Request, task_id: int) -> Task | JSONResponse:
        task = get_repository(request).get_task(task_id)
        if task is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )
        return task

    @app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
    def create_task(payload: TaskCreate, request: Request) -> Task:
        return get_repository(request).create_task(payload.title, False)

    @app.put("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
    def update_task(
        payload: TaskUpdate, request: Request, task_id: int
    ) -> Task | JSONResponse:
        task_repository = get_repository(request)
        if task_repository.get_task(task_id) is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )

        supplied = payload.model_fields_set
        if not supplied or supplied.isdisjoint({"title", "done"}):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Request body must include title and/or done"},
            )

        task = task_repository.update_task(
            task_id, title=payload.title, done=payload.done, fields=supplied
        )
        if task is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )
        return task

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(request: Request, task_id: int) -> Response:
        deleted = get_repository(request).delete_task(task_id)
        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()