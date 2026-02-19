from __future__ import annotations

from app.engine import rule_engine, rule_loader


def test_missing_required_field(monkeypatch):
    monkeypatch.setattr(
        rule_engine,
        "load_rules_for",
        lambda _regulation, db=None: [
            {
                "id": "req-product-id",
                "jsonpath": "$.product.id",
                "required": True,
                "severity": "error",
                "message": "Product id is required",
                "remediation": "Add product.id",
            }
        ],
    )

    result = rule_engine.evaluate_payload({"product": {}}, ["ESPR"])
    assert result["status"] == "non-compliant"
    assert len(result["violations"]) == 1
    assert result["violations"][0]["id"] == "req-product-id"
    assert result["violations"][0]["remediation"] == "Add product.id"


def test_constraint_type_range_and_enum(monkeypatch):
    monkeypatch.setattr(
        rule_engine,
        "load_rules_for",
        lambda _regulation, db=None: [
            {
                "id": "weight-range",
                "jsonpath": "$.product.weight",
                "required": True,
                "severity": "error",
                "type": "number",
                "min": 1,
                "max": 10,
                "enum": [1, 2, 3],
                "remediation": "Set weight to an allowed numeric value",
            }
        ],
    )

    result = rule_engine.evaluate_payload({"product": {"weight": 0}}, ["ESPR"])
    assert result["status"] == "non-compliant"
    assert len(result["violations"]) >= 1
    assert all(item["id"] == "weight-range" for item in result["violations"])


def test_regex_recommended_yields_recommendation(monkeypatch):
    monkeypatch.setattr(
        rule_engine,
        "load_rules_for",
        lambda _regulation, db=None: [
            {
                "id": "sku-format",
                "jsonpath": "$.product.sku",
                "recommended": True,
                "severity": "warning",
                "pattern": r"^SKU-[A-Z0-9]{4}$",
                "message": "SKU format should be SKU-XXXX",
                "remediation": "Use SKU- prefixed identifier",
            }
        ],
    )

    result = rule_engine.evaluate_payload({"product": {"sku": "bad-sku"}}, ["ESPR"])
    assert result["status"] == "compliant"
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["id"] == "sku-format"


def test_cross_field_dependency(monkeypatch):
    monkeypatch.setattr(
        rule_engine,
        "load_rules_for",
        lambda _regulation, db=None: [
            {
                "id": "battery-needs-chemistry",
                "jsonpath": "$.battery",
                "required": True,
                "severity": "error",
                "requires": ["$.battery.chemistry"],
                "message": "Battery chemistry is required when battery data exists",
                "remediation": "Set battery.chemistry",
            }
        ],
    )

    result = rule_engine.evaluate_payload({"battery": {"serial": "X"}}, ["Battery Regulation"])
    assert result["status"] == "non-compliant"
    assert len(result["violations"]) == 1
    assert result["violations"][0]["path"] == "$.battery.chemistry"


def test_if_then_conditional_requirement(monkeypatch):
    monkeypatch.setattr(
        rule_engine,
        "load_rules_for",
        lambda _regulation, db=None: [
            {
                "id": "serial-requires-manufacturer",
                "if": "$.battery.serial",
                "then_required": ["$.battery.manufacturer"],
                "required": True,
                "severity": "error",
                "message": "Manufacturer is required when serial is present",
                "remediation": "Set battery.manufacturer",
            }
        ],
    )

    result = rule_engine.evaluate_payload({"battery": {"serial": "ABC-123"}}, ["Battery Regulation"])
    assert result["status"] == "non-compliant"
    assert len(result["violations"]) == 1
    assert result["violations"][0]["level"] == "conditional"
    assert result["violations"][0]["path"] == "$.battery.manufacturer"


def test_validate_ruleset_checks_new_constraint_shapes():
    rules = [
        {
            "id": "bad-rule",
            "jsonpath": "$.product",
            "type": "decimal",  # invalid
            "enum": "not-a-list",
            "pattern": "(",  # invalid regex
            "min": "0",  # invalid numeric type
            "if": 123,
            "then_required": [123],
            "requires": [],
        }
    ]

    errors = rule_loader.validate_ruleset(rules)
    assert errors
    assert any("type must be one of" in err for err in errors)
    assert any("enum must be a non-empty list" in err for err in errors)
    assert any("invalid regex" in err for err in errors)
    assert any("min must be numeric" in err for err in errors)
    assert any("if must be a jsonpath string" in err for err in errors)
