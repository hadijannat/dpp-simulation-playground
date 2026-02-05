from typing import Dict


def evaluate_policy(policy: Dict, purpose: str) -> bool:
    for perm in policy.get("permission", []):
        constraint = perm.get("constraint", {})
        if constraint.get("leftOperand") == "purpose" and constraint.get("rightOperand") == purpose:
            return True
    return False
