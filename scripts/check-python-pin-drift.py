#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONSTRAINTS = ROOT / "requirements" / "constraints.txt"
SERVICES_DIR = ROOT / "services"

TARGET_PACKAGES = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "redis",
    "requests",
    "httpx",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-instrumentation-fastapi",
}


def parse_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pins[name.strip().lower()] = version.strip()
    return pins


def main() -> int:
    if not CONSTRAINTS.exists():
        print(f"Missing constraints file: {CONSTRAINTS}", file=sys.stderr)
        return 1

    constraints = parse_pins(CONSTRAINTS)
    failures: list[str] = []

    for req_file in sorted(SERVICES_DIR.glob("*/requirements.txt")):
        pins = parse_pins(req_file)
        for pkg in TARGET_PACKAGES:
            if pkg not in pins:
                continue
            expected = constraints.get(pkg)
            actual = pins[pkg]
            if expected is None:
                failures.append(f"{req_file}: {pkg} pinned to {actual}, but package missing in constraints.txt")
                continue
            if actual != expected:
                failures.append(f"{req_file}: {pkg} pinned to {actual}, expected {expected}")

    if failures:
        print("Python pin drift detected:\n", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("No Python pin drift detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
