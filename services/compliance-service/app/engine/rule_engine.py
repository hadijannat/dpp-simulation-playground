from typing import Dict, List, Any
from jsonpath_ng import parse
from .rule_loader import load_rules_for


def evaluate_payload(data: Dict[str, Any], regulations: List[str]) -> Dict[str, Any]:
    violations = []
    warnings = []
    for regulation in regulations:
        for rule in load_rules_for(regulation):
            path = rule.get("jsonpath")
            required = rule.get("required", False)
            recommended = rule.get("recommended", False)
            severity = rule.get("severity", "warning")
            when = rule.get("when")
            if when:
                when_matches = parse(when).find(data)
                if not when_matches:
                    continue
            matches = parse(path).find(data) if path else []
            if (required or recommended) and not matches:
                target = {
                    "id": rule.get("id"),
                    "message": rule.get("message", "Missing required field"),
                    "regulation": regulation,
                }
                if required and severity == "error":
                    violations.append(target)
                else:
                    warnings.append(target)
    status = "compliant" if not violations else "non-compliant"
    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": [],
    }
