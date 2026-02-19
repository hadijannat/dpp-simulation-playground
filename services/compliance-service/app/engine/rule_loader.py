import os
import re
import yaml
from typing import Any, Dict, List

from jsonpath_ng import parse
from sqlalchemy import func
from sqlalchemy.orm import Session

from services.shared.models.compliance_rule_version import ComplianceRuleVersion

RULES_DIR = os.getenv("RULES_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "compliance-rules"))


def _normalize_regulation(value: str) -> str:
    return (value or "").strip().lower()


def _load_rules_file(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def _load_rules_for_from_files(regulation: str) -> List[Dict]:
    filename = f"{regulation.lower().replace(' ', '-')}-v1.yaml"
    path = os.path.join(RULES_DIR, filename)
    if not os.path.exists(path):
        return []
    return _load_rules_file(path)


def get_active_rule_version(db: Session, regulation: str) -> ComplianceRuleVersion | None:
    normalized = _normalize_regulation(regulation)
    return (
        db.query(ComplianceRuleVersion)
        .filter(func.lower(ComplianceRuleVersion.regulation) == normalized)
        .order_by(ComplianceRuleVersion.effective_from.desc(), ComplianceRuleVersion.created_at.desc())
        .first()
    )


def list_rule_versions(
    db: Session,
    regulation: str | None = None,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ComplianceRuleVersion], int]:
    query = db.query(ComplianceRuleVersion)
    if regulation:
        normalized = _normalize_regulation(regulation)
        query = query.filter(func.lower(ComplianceRuleVersion.regulation) == normalized)
    total = query.count()
    items = (
        query.order_by(
            ComplianceRuleVersion.regulation.asc(),
            ComplianceRuleVersion.effective_from.desc(),
            ComplianceRuleVersion.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def load_rules_for(regulation: str, db: Session | None = None) -> List[Dict]:
    if db is not None:
        try:
            current = get_active_rule_version(db, regulation)
            if current and isinstance(current.rules, list):
                return current.rules
        except Exception:
            pass
    return _load_rules_for_from_files(regulation)


def load_all_rules(db: Session | None = None) -> Dict[str, List[Dict]]:
    if db is not None:
        try:
            rules_by_regulation: Dict[str, List[Dict]] = {}
            versions = db.query(ComplianceRuleVersion).order_by(ComplianceRuleVersion.effective_from.desc()).all()
            for version in versions:
                key = _normalize_regulation(version.regulation)
                if key in rules_by_regulation:
                    continue
                if isinstance(version.rules, list):
                    rules_by_regulation[key] = version.rules
            if rules_by_regulation:
                return rules_by_regulation
        except Exception:
            pass

    rules = {}
    for fname in os.listdir(RULES_DIR):
        if fname.endswith(".yaml"):
            path = os.path.join(RULES_DIR, fname)
            rules[fname] = _load_rules_file(path)
    return rules


def validate_ruleset(rules: Any) -> list[str]:
    errors: list[str] = []
    allowed_types = {"string", "number", "integer", "boolean", "object", "array"}
    if not isinstance(rules, list):
        return ["rules must be a list"]

    def _validate_jsonpath(path_value: str, label: str) -> None:
        try:
            parse(path_value)
        except Exception as exc:
            errors.append(f"{label}: invalid jsonpath '{path_value}': {exc}")

    def _validate_path_list(value: Any, label: str) -> None:
        if isinstance(value, str):
            _validate_jsonpath(value, label)
            return
        if not isinstance(value, list) or not value:
            errors.append(f"{label}: must be a non-empty string or list of jsonpaths")
            return
        for idx, item in enumerate(value):
            if not isinstance(item, str) or not item:
                errors.append(f"{label}[{idx}]: must be a jsonpath string")
                continue
            _validate_jsonpath(item, f"{label}[{idx}]")

    for index, rule in enumerate(rules):
        label = f"rule[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{label}: must be an object")
            continue
        if not rule.get("id"):
            errors.append(f"{label}: missing id")
        path = rule.get("jsonpath")
        if path:
            _validate_jsonpath(path, label)
        when = rule.get("when")
        if when:
            _validate_jsonpath(when, f"{label}:when")

        rule_type = rule.get("type")
        if rule_type is not None and rule_type not in allowed_types:
            errors.append(f"{label}: type must be one of {sorted(allowed_types)}")

        enum_values = rule.get("enum")
        if enum_values is not None and (not isinstance(enum_values, list) or not enum_values):
            errors.append(f"{label}: enum must be a non-empty list")

        for numeric_key in ("min", "max", "min_length", "max_length"):
            numeric_value = rule.get(numeric_key)
            if numeric_value is None:
                continue
            if not isinstance(numeric_value, (int, float)) or isinstance(numeric_value, bool):
                errors.append(f"{label}: {numeric_key} must be numeric")

        pattern = rule.get("pattern") or rule.get("regex")
        if pattern is not None:
            if not isinstance(pattern, str) or not pattern:
                errors.append(f"{label}: pattern/regex must be a non-empty string")
            else:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    errors.append(f"{label}: invalid regex '{pattern}': {exc}")

        if_value = rule.get("if")
        if if_value is not None:
            if not isinstance(if_value, str) or not if_value:
                errors.append(f"{label}: if must be a jsonpath string")
            else:
                _validate_jsonpath(if_value, f"{label}:if")

        if "requires" in rule:
            _validate_path_list(rule.get("requires"), f"{label}:requires")
        if "then_required" in rule:
            _validate_path_list(rule.get("then_required"), f"{label}:then_required")
        if "then" in rule:
            _validate_path_list(rule.get("then"), f"{label}:then")
    return errors
