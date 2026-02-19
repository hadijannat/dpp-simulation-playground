from __future__ import annotations

import re
from typing import Any

from jsonpath_ng import parse
from sqlalchemy.orm import Session

from .rule_loader import load_rules_for

_ALLOWED_TYPES: dict[str, tuple[type[Any], ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "object": (dict,),
    "array": (list,),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _find_matches(path: str | None, data: dict[str, Any]) -> list[Any]:
    if not path:
        return []
    try:
        return parse(path).find(data)
    except Exception:
        return []


def _normalize_then_paths(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def _classify_level(*, recommended: bool, conditional: bool) -> str:
    if recommended:
        return "recommended"
    if conditional:
        return "conditional"
    return "required"


def _append_issue(
    *,
    violations: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    rule: dict[str, Any],
    regulation: str,
    path: str | None,
    level: str,
    default_message: str,
) -> None:
    severity = rule.get("severity", "warning")
    issue = {
        "id": rule.get("id"),
        "message": rule.get("message", default_message),
        "regulation": regulation,
        "jsonpath": path,
        "path": path,
        "severity": severity,
        "level": level,
        "remediation": rule.get("remediation"),
    }
    if level == "recommended":
        recommendations.append(issue)
    elif severity == "error":
        violations.append(issue)
    else:
        warnings.append(issue)


def _validate_constraints(rule: dict[str, Any], value: Any) -> list[str]:
    failures: list[str] = []

    expected_type = rule.get("type")
    if isinstance(expected_type, str):
        allowed = _ALLOWED_TYPES.get(expected_type)
        if allowed:
            if expected_type == "number":
                if not _is_number(value):
                    failures.append("value must be a number")
            elif expected_type == "integer":
                if not isinstance(value, int) or isinstance(value, bool):
                    failures.append("value must be an integer")
            elif not isinstance(value, allowed):
                failures.append(f"value must be of type '{expected_type}'")

    enum_values = rule.get("enum")
    if isinstance(enum_values, list) and enum_values and value not in enum_values:
        failures.append(f"value must be one of {enum_values}")

    pattern = rule.get("pattern") or rule.get("regex")
    if isinstance(pattern, str) and pattern:
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            failures.append(f"value must match pattern '{pattern}'")

    min_value = rule.get("min")
    max_value = rule.get("max")
    if min_value is not None or max_value is not None:
        if not _is_number(value):
            failures.append("value must be numeric for min/max checks")
        else:
            if min_value is not None and value < min_value:
                failures.append(f"value must be >= {min_value}")
            if max_value is not None and value > max_value:
                failures.append(f"value must be <= {max_value}")

    min_length = rule.get("min_length")
    max_length = rule.get("max_length")
    if min_length is not None or max_length is not None:
        if not isinstance(value, (str, list, dict)):
            failures.append("value must support length checks")
        else:
            current_len = len(value)
            if min_length is not None and current_len < min_length:
                failures.append(f"length must be >= {min_length}")
            if max_length is not None and current_len > max_length:
                failures.append(f"length must be <= {max_length}")

    return failures


def evaluate_payload(data: dict[str, Any], regulations: list[str], db: Session | None = None) -> dict[str, Any]:
    data = data or {}
    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    for regulation in regulations:
        for rule in load_rules_for(regulation, db=db):
            path = rule.get("jsonpath")
            required = bool(rule.get("required", False))
            recommended = bool(rule.get("recommended", False))
            when = rule.get("when")

            # Existing guard condition: evaluate rule only when the guard matches.
            if when:
                when_matches = _find_matches(when, data)
                if not when_matches:
                    continue

            matches = _find_matches(path, data) if path else []
            level = _classify_level(recommended=recommended, conditional=bool(when and required))

            # Presence validation (required/recommended).
            if (required or recommended) and path and not matches:
                _append_issue(
                    violations=violations,
                    warnings=warnings,
                    recommendations=recommendations,
                    rule=rule,
                    regulation=regulation,
                    path=path,
                    level=level,
                    default_message="Missing required field",
                )
                continue

            # Value constraints validation.
            if matches:
                for match in matches:
                    failures = _validate_constraints(rule, match.value)
                    for failure in failures:
                        _append_issue(
                            violations=violations,
                            warnings=warnings,
                            recommendations=recommendations,
                            rule=rule,
                            regulation=regulation,
                            path=path,
                            level=_classify_level(recommended=recommended, conditional=False),
                            default_message=failure,
                        )

            # Cross-field dependencies: if this rule path is present, required companion paths must exist.
            requires = _normalize_then_paths(rule.get("requires"))
            if matches and requires:
                for required_path in requires:
                    if _find_matches(required_path, data):
                        continue
                    _append_issue(
                        violations=violations,
                        warnings=warnings,
                        recommendations=recommendations,
                        rule=rule,
                        regulation=regulation,
                        path=required_path,
                        level=_classify_level(recommended=recommended, conditional=False),
                        default_message=f"Missing dependent field '{required_path}'",
                    )

            # Conditional if/then requirement.
            if_expr = rule.get("if")
            then_paths = _normalize_then_paths(rule.get("then_required") or rule.get("then"))
            if if_expr and then_paths:
                if_matches = _find_matches(if_expr, data)
                if if_matches:
                    for then_path in then_paths:
                        if _find_matches(then_path, data):
                            continue
                        _append_issue(
                            violations=violations,
                            warnings=warnings,
                            recommendations=recommendations,
                            rule=rule,
                            regulation=regulation,
                            path=then_path,
                            level=_classify_level(recommended=recommended, conditional=True),
                            default_message=f"Conditional requirement missing '{then_path}'",
                        )

    status = "compliant" if not violations else "non-compliant"
    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
        "summary": {
            "violations": len(violations),
            "warnings": len(warnings),
            "recommendations": len(recommendations),
        },
    }
