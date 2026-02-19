from __future__ import annotations

from app.odrl.policy_evaluator import evaluate_policy


def test_policy_eq_operator_allows_matching_purpose():
    policy = {
        "permission": [
            {
                "constraint": {
                    "leftOperand": "purpose",
                    "operator": "eq",
                    "rightOperand": "analytics",
                }
            }
        ]
    }
    assert evaluate_policy(policy, "analytics") is True
    assert evaluate_policy(policy, "marketing") is False


def test_policy_in_operator_supports_list_values():
    policy = {
        "permission": [
            {
                "constraint": {
                    "leftOperand": "purpose",
                    "operator": "in",
                    "rightOperand": ["analytics", "quality"],
                }
            }
        ]
    }
    assert evaluate_policy(policy, "quality") is True
    assert evaluate_policy(policy, "compliance") is False


def test_policy_and_or_composition():
    policy = {
        "permission": [
            {
                "constraint": {
                    "and": [
                        {"leftOperand": "purpose", "operator": "eq", "rightOperand": "analytics"},
                        {
                            "or": [
                                {"leftOperand": "region", "operator": "eq", "rightOperand": "eu"},
                                {"leftOperand": "region", "operator": "eq", "rightOperand": "us"},
                            ]
                        },
                    ]
                }
            }
        ]
    }

    assert evaluate_policy(policy, "analytics", context={"region": "eu"}) is True
    assert evaluate_policy(policy, "analytics", context={"region": "apac"}) is False


def test_prohibition_overrides_permission():
    policy = {
        "permission": [
            {
                "constraint": {
                    "leftOperand": "purpose",
                    "operator": "eq",
                    "rightOperand": "analytics",
                }
            }
        ],
        "prohibition": [
            {
                "constraint": {
                    "leftOperand": "country",
                    "operator": "eq",
                    "rightOperand": "restricted",
                }
            }
        ],
    }
    assert evaluate_policy(policy, "analytics", context={"country": "de"}) is True
    assert evaluate_policy(policy, "analytics", context={"country": "restricted"}) is False


def test_obligation_requires_matching_constraint():
    policy = {
        "permission": [
            {
                "constraint": {
                    "leftOperand": "purpose",
                    "operator": "eq",
                    "rightOperand": "analytics",
                },
                "duty": [
                    {
                        "constraint": {
                            "leftOperand": "retention_days",
                            "operator": "lte",
                            "rightOperand": 30,
                        }
                    }
                ],
            }
        ]
    }

    assert evaluate_policy(policy, "analytics", context={"retention_days": 20}) is True
    assert evaluate_policy(policy, "analytics", context={"retention_days": 90}) is False
