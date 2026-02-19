from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ..schemas.story_schema import StoryDefinition

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DATA_DIR = os.path.join(ROOT_DIR, "data", "stories")
DATA_DIR: str = os.getenv("STORY_DATA_DIR") or DEFAULT_DATA_DIR

_CACHE: dict[str, dict[str, Any]] = {}


def _resolve_data_dir(data_dir: str | None = None) -> str:
    return data_dir or os.getenv("STORY_DATA_DIR") or DATA_DIR


def _story_files_signature(resolved_dir: str) -> tuple[tuple[str, int, int], ...]:
    parts: list[tuple[str, int, int]] = []
    for filename in sorted(os.listdir(resolved_dir)):
        if not filename.endswith(".yaml"):
            continue
        if filename == "schema.yaml":
            continue
        path = os.path.join(resolved_dir, filename)
        stat = os.stat(path)
        parts.append((filename, int(stat.st_mtime_ns), int(stat.st_size)))
    return tuple(parts)


def _decorate(story: dict[str, Any]) -> dict[str, Any]:
    code = story.get("code", "")
    parts = code.split("-")
    epic_code = None
    order_index = None
    if len(parts) >= 3 and parts[1].isdigit():
        epic_code = f"EPIC-{parts[1]}"
        try:
            order_index = int(parts[2])
        except ValueError:
            order_index = None
    return {
        **story,
        "epic_code": epic_code,
        "order_index": order_index,
        "roles": story.get("roles")
        or ["manufacturer", "regulator", "consumer", "recycler", "developer"],
        "difficulty": story.get("difficulty") or "intermediate",
        "story_version": story.get("story_version") or 1,
    }


def _validate_story(raw_story: Any, *, source: str, index: int) -> dict[str, Any]:
    try:
        validated = StoryDefinition.model_validate(raw_story)
    except ValidationError as exc:
        raise ValueError(
            f"{source}: invalid story at index {index}: {exc.errors(include_url=False)}"
        ) from exc
    return validated.model_dump(exclude_none=True)


def _load_all(data_dir: str | None = None) -> list[dict[str, Any]]:
    resolved_dir = _resolve_data_dir(data_dir)
    if not os.path.exists(resolved_dir):
        raise KeyError(f"Story data directory not found: {resolved_dir}")

    signature = _story_files_signature(resolved_dir)
    cached = _CACHE.get(resolved_dir)
    if cached and cached.get("signature") == signature:
        return copy.deepcopy(cached.get("stories", []))

    all_stories: list[dict[str, Any]] = []
    for filename, _, _ in signature:
        file_path = os.path.join(resolved_dir, filename)
        with open(file_path, "r", encoding="utf-8") as handle:
            parsed = yaml.safe_load(handle) or []
        if not isinstance(parsed, list):
            raise ValueError(f"{file_path}: story file must contain a list of stories")
        for index, raw_story in enumerate(parsed):
            validated = _validate_story(raw_story, source=file_path, index=index)
            all_stories.append(_decorate(validated))

    _CACHE[resolved_dir] = {
        "signature": signature,
        "stories": copy.deepcopy(all_stories),
    }
    return all_stories


def load_story(code: str, *, data_dir: str | None = None) -> dict[str, Any]:
    for story in _load_all(data_dir=data_dir):
        if story.get("code") == code:
            return story
    raise KeyError(f"Story {code} not found")


def list_stories(*, data_dir: str | None = None) -> list[dict[str, Any]]:
    return _load_all(data_dir=data_dir)


def lint_stories(*, data_dir: str | None = None) -> list[str]:
    errors: list[str] = []
    resolved_dir = _resolve_data_dir(data_dir)
    if not Path(resolved_dir).exists():
        return [f"Story data directory not found: {resolved_dir}"]
    try:
        _load_all(data_dir=resolved_dir)
    except (KeyError, ValueError) as exc:
        errors.append(str(exc))
    return errors
