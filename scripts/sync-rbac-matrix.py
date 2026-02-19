#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "services" / "shared" / "rbac_matrix.yaml"

SERVICES = {
    "aas-adapter": ROOT / "services" / "aas-adapter",
    "collaboration-service": ROOT / "services" / "collaboration-service",
    "compliance-service": ROOT / "services" / "compliance-service",
    "edc-simulator": ROOT / "services" / "edc-simulator",
    "gamification-service": ROOT / "services" / "gamification-service",
    "platform-api": ROOT / "services" / "platform-api",
    "platform-core": ROOT / "services" / "platform-core",
    "simulation-engine": ROOT / "services" / "simulation-engine",
}

SNIPPET = """
import json
import sys
from pathlib import Path

root = Path(r"{root}")
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.main import app
from services.shared.rbac_matrix import extract_route_role_map

print(json.dumps(extract_route_role_map(app), sort_keys=True))
""".strip()


def collect_service_map(service_dir: Path) -> dict[str, list[str]]:
    snippet = SNIPPET.format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=service_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip() or "{}")


def build_matrix() -> dict:
    services: dict[str, dict[str, list[str]]] = {}
    for service_name, service_dir in SERVICES.items():
        services[service_name] = collect_service_map(service_dir)
    return {"services": services}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate RBAC matrix from route handlers.")
    parser.add_argument("--check", action="store_true", help="Fail if matrix file differs from generated output.")
    args = parser.parse_args()

    generated = build_matrix()
    rendered = yaml.safe_dump(generated, sort_keys=True)

    if args.check:
        if not MATRIX_PATH.exists():
            print(f"Missing RBAC matrix: {MATRIX_PATH}", file=sys.stderr)
            return 1
        current = MATRIX_PATH.read_text(encoding="utf-8")
        if current != rendered:
            print("RBAC matrix is out of date. Run scripts/sync-rbac-matrix.py", file=sys.stderr)
            return 1
        print("RBAC matrix is up to date.")
        return 0

    MATRIX_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {MATRIX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
