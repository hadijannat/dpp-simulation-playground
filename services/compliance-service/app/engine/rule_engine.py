from typing import Dict, List, Any
from jsonpath_ng import parse
from sqlalchemy.orm import Session

from .rule_loader import load_rules_for


def evaluate_payload(data: Dict[str, Any], regulations: List[str], db: Session | None = None) -> Dict[str, Any]:
    data = data or {}
    violations = []
    warnings = []
    recommendations = []
    for regulation in regulations:
        for rule in load_rules_for(regulation, db=db):
            path = rule.get("jsonpath")
            required = rule.get("required", False)
            recommended = rule.get("recommended", False)
            severity = rule.get("severity", "warning")
            when = rule.get("when")
            if when:
                try:
                    when_matches = parse(when).find(data)
                except Exception:
                    continue
                if not when_matches:
                    continue
            try:
                matches = parse(path).find(data) if path else []
            except Exception:
                continue
            is_missing = (required or recommended) and not matches
            if not is_missing:
                continue
            level = "required"
            if recommended:
                level = "recommended"
            if when and required:
                level = "conditional"
            target = {
                "id": rule.get("id"),
                "message": rule.get("message", "Missing required field"),
                "regulation": regulation,
                "jsonpath": path,
                "path": path,
                "severity": severity,
                "level": level,
                "remediation": rule.get("remediation"),
            }
            if level == "recommended":
                recommendations.append(target)
            elif severity == "error":
                violations.append(target)
            else:
                warnings.append(target)
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
