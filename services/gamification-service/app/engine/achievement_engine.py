import yaml
import os

DEFINITIONS = os.path.join(os.path.dirname(__file__), "..", "definitions", "achievements.yaml")


def load_achievements():
    with open(DEFINITIONS, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []
