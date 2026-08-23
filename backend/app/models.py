from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TaskResponse(BaseModel):
    """The stable Assignment 1/2 task representation."""

    id: int = Field(ge=1)
    title: str
    description: str
    completed: bool


class TaskInput(BaseModel):
    """Payload for creating a task."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    completed: bool = False

    @field_validator("title")
    @classmethod
    def title_must_contain_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("title must contain text")
        return normalized


class TaskUpdate(BaseModel):
    """Partial update payload; at least one valid property is required."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None

    @model_validator(mode="after")
    def require_a_non_null_field(self) -> "TaskUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one task field is required")
        if any(
            getattr(self, field_name) is None
            for field_name in self.model_fields_set
        ):
            raise ValueError("task fields cannot be null")
        if "title" in self.model_fields_set:
            normalized = self.title.strip() if self.title else ""
            if not normalized:
                raise ValueError("title must contain text")
            self.title = normalized
        return self


class ErrorResponse(BaseModel):
    error: str