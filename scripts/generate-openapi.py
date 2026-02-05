#!/usr/bin/env python
import importlib
import sys
from pathlib import Path
import yaml

SERVICES = {
    "simulation-engine": {
        "path": Path("services/simulation-engine"),
        "module": "app.main",
        "output": Path("docs/api/openapi/simulation-engine.yaml"),
    },
    "compliance-service": {
        "path": Path("services/compliance-service"),
        "module": "app.main",
        "output": Path("docs/api/openapi/compliance-service.yaml"),
    },
    "gamification-service": {
        "path": Path("services/gamification-service"),
        "module": "app.main",
        "output": Path("docs/api/openapi/gamification-service.yaml"),
    },
    "edc-simulator": {
        "path": Path("services/edc-simulator"),
        "module": "app.main",
        "output": Path("docs/api/openapi/edc-simulator.yaml"),
    },
    "collaboration-service": {
        "path": Path("services/collaboration-service"),
        "module": "app.main",
        "output": Path("docs/api/openapi/collaboration-service.yaml"),
    },
}


def load_app(service):
    service_path = service["path"].resolve()
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(service_path))
    try:
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                sys.modules.pop(name, None)
        module = importlib.import_module(service["module"])
        return getattr(module, "app")
    finally:
        sys.path.remove(str(service_path))
        sys.path.remove(str(repo_root))


def main():
    for name, info in SERVICES.items():
        app = load_app(info)
        spec = app.openapi()
        info["output"].parent.mkdir(parents=True, exist_ok=True)
        info["output"].write_text(yaml.safe_dump(spec, sort_keys=False))
        print(f"Wrote {info['output']}")


if __name__ == "__main__":
    main()
