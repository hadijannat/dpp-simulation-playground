#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

APPS = {
    "simulation-engine": ROOT / "services" / "simulation-engine",
    "compliance-service": ROOT / "services" / "compliance-service",
    "gamification-service": ROOT / "services" / "gamification-service",
    "edc-simulator": ROOT / "services" / "edc-simulator",
    "collaboration-service": ROOT / "services" / "collaboration-service",
    "platform-api": ROOT / "services" / "platform-api",
    "platform-core": ROOT / "services" / "platform-core",
    "aas-adapter": ROOT / "services" / "aas-adapter",
}

OUTPUT_DIR = ROOT / "docs" / "api" / "openapi"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_SNIPPET = """
import json
from app.main import app
print(json.dumps(app.openapi()))
""".strip()


def export_openapi(service_name: str, service_dir: Path) -> dict:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{ROOT}:{service_dir}" if not pythonpath else f"{ROOT}:{service_dir}:{pythonpath}"
    )
    result = subprocess.run(
        ["python", "-c", EXPORT_SNIPPET],
        cwd=service_dir,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return yaml.safe_load(result.stdout)


def main():
    for service_name, service_dir in APPS.items():
        spec = export_openapi(service_name, service_dir)
        output_path = OUTPUT_DIR / f"{service_name}.yaml"
        output_path.write_text(yaml.safe_dump(spec, sort_keys=False))
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
