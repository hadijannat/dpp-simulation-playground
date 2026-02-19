from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI
from fastapi.routing import APIRoute


MATRIX_PATH = Path(__file__).resolve().with_name("rbac_matrix.yaml")


def load_matrix() -> dict[str, Any]:
    if not MATRIX_PATH.exists():
        return {"services": {}}
    data = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8")) or {}
    if "services" not in data:
        data["services"] = {}
    return data


def load_service_matrix(service_name: str) -> dict[str, list[str]]:
    matrix = load_matrix()
    services = matrix.get("services", {})
    return {str(k): list(v) for k, v in (services.get(service_name, {}) or {}).items()}


def _extract_literal_roles(node: ast.AST, module: Any) -> list[str] | None:
    if isinstance(node, (ast.List, ast.Tuple)):
        roles: list[str] = []
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                roles.append(item.value)
            else:
                return None
        return roles
    if isinstance(node, ast.Name):
        value = getattr(module, node.id, None)
        if isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
            return list(value)
    return None


def extract_required_roles(endpoint: Any) -> list[str] | None:
    try:
        source = textwrap.dedent(inspect.getsource(endpoint))
    except (OSError, TypeError):
        return None
    module = inspect.getmodule(endpoint)
    if module is None:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name: str | None = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if func_name != "require_roles" or len(node.args) < 2:
            continue
        roles = _extract_literal_roles(node.args[1], module)
        if roles is not None:
            return sorted(set(roles))
    return None


def extract_route_role_map(app: FastAPI) -> dict[str, list[str]]:
    route_roles: dict[str, list[str]] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        roles = extract_required_roles(route.endpoint)
        if roles is None:
            continue
        methods = sorted(method for method in route.methods if method not in {"HEAD", "OPTIONS"})
        for method in methods:
            route_roles[f"{method} {route.path}"] = roles
    return dict(sorted(route_roles.items()))
