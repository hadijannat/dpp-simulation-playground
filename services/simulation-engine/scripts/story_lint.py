#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = Path(__file__).resolve().parents[1]
for path in (ROOT, SERVICE_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from app.core.story_loader import lint_stories  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate simulation story definitions.")
    parser.add_argument("--data-dir", default=None, help="Optional story data directory override.")
    args = parser.parse_args()

    errors = lint_stories(data_dir=args.data_dir)
    if errors:
        print("Story lint failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("Story lint passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
