import os
import yaml
from typing import Dict, List

RULES_DIR = os.getenv("RULES_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "compliance-rules"))


def load_rules_for(regulation: str) -> List[Dict]:
    filename = f"{regulation.lower().replace(' ', '-')}-v1.yaml"
    path = os.path.join(RULES_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def load_all_rules() -> Dict[str, List[Dict]]:
    rules = {}
    for fname in os.listdir(RULES_DIR):
        if fname.endswith(".yaml"):
            with open(os.path.join(RULES_DIR, fname), "r", encoding="utf-8") as handle:
                rules[fname] = yaml.safe_load(handle) or []
    return rules
