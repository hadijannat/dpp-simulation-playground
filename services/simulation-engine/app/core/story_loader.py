import os
import yaml
from typing import Dict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_DATA_DIR = os.path.join(ROOT_DIR, "data", "stories")
DATA_DIR = os.getenv("STORY_DATA_DIR", DEFAULT_DATA_DIR)


def load_story(code: str) -> Dict:
    if not os.path.exists(DATA_DIR):
        raise KeyError(f"Story data directory not found: {DATA_DIR}")
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".yaml"):
            continue
        with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as handle:
            stories = yaml.safe_load(handle) or []
            for story in stories:
                if story.get("code") == code:
                    return story
    raise KeyError(f"Story {code} not found")
