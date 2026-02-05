#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_app(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "app")


APPS = {
    "simulation-engine": ROOT / "services" / "simulation-engine" / "app" / "main.py",
    "compliance-service": ROOT / "services" / "compliance-service" / "app" / "main.py",
    "gamification-service": ROOT / "services" / "gamification-service" / "app" / "main.py",
    "edc-simulator": ROOT / "services" / "edc-simulator" / "app" / "main.py",
    "collaboration-service": ROOT / "services" / "collaboration-service" / "app" / "main.py",
}

OUTPUT_DIR = ROOT / "docs" / "api" / "openapi"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    for name, path in APPS.items():
        app = load_app(path)
        spec = app.openapi()
        out = OUTPUT_DIR / f"{name}.yaml"
        out.write_text(yaml.safe_dump(spec, sort_keys=False))
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
