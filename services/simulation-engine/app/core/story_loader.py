import os
import yaml
from typing import Dict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_DATA_DIR = os.path.join(ROOT_DIR, "data", "stories")
DATA_DIR = os.getenv("STORY_DATA_DIR", DEFAULT_DATA_DIR)


def _decorate(story: Dict) -> Dict:
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
        "roles": story.get("roles") or ["manufacturer", "regulator", "consumer", "recycler", "developer"],
        "difficulty": story.get("difficulty") or "intermediate",
    }


def _load_all() -> list[Dict]:
    if not os.path.exists(DATA_DIR):
        raise KeyError(f"Story data directory not found: {DATA_DIR}")
    all_stories: list[Dict] = []
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".yaml"):
            continue
        with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as handle:
            stories = yaml.safe_load(handle) or []
            if isinstance(stories, list):
                all_stories.extend(stories)
    return [_decorate(item) for item in all_stories]


def load_story(code: str) -> Dict:
    for story in _load_all():
        if story.get("code") == code:
            return story
    raise KeyError(f"Story {code} not found")


def list_stories() -> list[Dict]:
    return _load_all()
