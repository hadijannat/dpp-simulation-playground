from __future__ import annotations

from typing import Any


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _operand_key(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    token = value.split(":")[-1].strip()
    return token


def _context_value(context: dict[str, Any], operand: Any) -> Any:
    key = _operand_key(operand)
    if not key:
        return None
    if key in context:
        return context[key]
    prefixed = f"odrl:{key}"
    if prefixed in context:
        return context[prefixed]
    return None


def _normalize_operator(value: Any) -> str:
    if not isinstance(value, str):
        return "eq"
    return value.split(":")[-1].strip().lower()


def _normalize_right_values(value: Any) -> list[Any]:
    if isinstance(value, dict) and "@list" in value:
        return _as_list(value.get("@list"))
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _eval_operator(operator: str, left: Any, right: Any) -> bool:
    values = _normalize_right_values(right)

    if operator == "eq":
        return any(left == item for item in values)
    if operator == "neq":
        return all(left != item for item in values)
    if operator == "in":
        return any(left == item for item in values)
    if operator in {"nin", "notin"}:
        return all(left != item for item in values)

    if operator in {"gt", "gte", "lt", "lte"}:
        if not isinstance(left, (int, float)) or isinstance(left, bool):
            return False
        comparisons = [item for item in values if isinstance(item, (int, float)) and not isinstance(item, bool)]
        if not comparisons:
            return False
        right_num = comparisons[0]
        if operator == "gt":
            return left > right_num
        if operator == "gte":
            return left >= right_num
        if operator == "lt":
            return left < right_num
        return left <= right_num

    if operator in {"contains", "includes"}:
        if isinstance(left, str):
            return any(str(item) in left for item in values)
        if isinstance(left, (list, tuple, set)):
            return any(item in left for item in values)
        if isinstance(left, dict):
            return any(item in left for item in values)
        return False

    return False


def _evaluate_constraint(constraint: Any, context: dict[str, Any]) -> bool:
    if constraint is None:
        return True

    if isinstance(constraint, list):
        return all(_evaluate_constraint(item, context) for item in constraint)

    if not isinstance(constraint, dict):
        return False

    for key in ("and", "odrl:and"):
        if key in constraint:
            return all(_evaluate_constraint(item, context) for item in _as_list(constraint.get(key)))
    for key in ("or", "odrl:or"):
        if key in constraint:
            return any(_evaluate_constraint(item, context) for item in _as_list(constraint.get(key)))
    for key in ("xone", "odrl:xone"):
        if key in constraint:
            matches = [
                _evaluate_constraint(item, context)
                for item in _as_list(constraint.get(key))
            ]
            return sum(1 for item in matches if item) == 1

    left = _context_value(context, constraint.get("leftOperand"))
    operator = _normalize_operator(constraint.get("operator"))
    right = constraint.get("rightOperand")

    if left is None:
        return False
    return _eval_operator(operator, left, right)


def _rule_constraints_hold(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    constraints = rule.get("constraint")
    return _evaluate_constraint(constraints, context)


def _obligations_hold(policy: dict[str, Any], permission: dict[str, Any], context: dict[str, Any]) -> bool:
    obligations = []
    obligations.extend(_as_list(permission.get("duty")))
    obligations.extend(_as_list(permission.get("obligation")))
    obligations.extend(_as_list(policy.get("obligation")))

    for obligation in obligations:
        if not isinstance(obligation, dict):
            return False
        if not _rule_constraints_hold(obligation, context):
            return False
    return True


def evaluate_policy(policy: dict[str, Any], purpose: str, context: dict[str, Any] | None = None) -> bool:
    context_map: dict[str, Any] = {"purpose": purpose}
    if isinstance(context, dict):
        context_map.update(context)

    permissions = [item for item in _as_list(policy.get("permission")) if isinstance(item, dict)]
    if not permissions:
        return False

    permission_allowed = False
    for permission in permissions:
        if not _rule_constraints_hold(permission, context_map):
            continue
        if not _obligations_hold(policy, permission, context_map):
            continue
        permission_allowed = True
        break

    if not permission_allowed:
        return False

    prohibitions = [item for item in _as_list(policy.get("prohibition")) if isinstance(item, dict)]
    for prohibition in prohibitions:
        if _rule_constraints_hold(prohibition, context_map):
            return False

    return True
