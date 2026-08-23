from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class Task(BaseModel):
    """The unchanged Assignment 1/2 task representation."""

    id: int
    title: str | None
    done: bool | None


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    @field_validator("title")
    @classmethod
    def title_cannot_be_blank(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title must not be blank")
        return title


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    done: bool | None = None

    @field_validator("title")
    @classmethod
    def title_cannot_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if not title:
            raise ValueError("title must not be blank")
        return title


class ErrorResponse(BaseModel):
    error: str