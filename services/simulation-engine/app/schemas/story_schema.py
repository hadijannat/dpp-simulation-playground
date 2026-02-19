from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StoryStepDefinition(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


class StoryDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")

    story_version: int = 1
    code: str
    title: str
    description: str | None = None
    steps: list[StoryStepDefinition]
    inputs: dict[str, Any] | None = None
    validations: list[dict[str, Any]] | None = None
    role_constraints: list[str] | None = None
    roles: list[str] | None = None
    difficulty: str | None = None

    @field_validator("story_version")
    @classmethod
    def validate_story_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("story_version must be >= 1")
        return value

    @field_validator("code", "title")
    @classmethod
    def non_empty_string(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("value must be non-empty")
        return value.strip()


# Backward-compatible alias.
Story = StoryDefinition
