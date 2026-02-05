import os
import yaml
from typing import List, Dict

DATA_DIR = os.getenv("STORY_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "stories"))


def load_story(code: str) -> Dict:
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".yaml"):
            continue
        with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as handle:
            stories = yaml.safe_load(handle) or []
            for story in stories:
                if story.get("code") == code:
                    return story
    raise KeyError(f"Story {code} not found")
