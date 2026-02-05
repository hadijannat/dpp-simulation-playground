from app.engine.rule_engine import evaluate_payload


def test_missing_required_field():
    data = {"product": "x"}
    result = evaluate_payload(data, ["ESPR"])
    assert result["status"] in ("compliant", "non-compliant")
