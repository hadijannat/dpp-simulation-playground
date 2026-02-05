from typing import Dict


def build_policy(purpose: str) -> Dict:
    return {
        "@type": "odrl:Offer",
        "permission": [
            {
                "action": "use",
                "constraint": {
                    "leftOperand": "purpose",
                    "operator": "eq",
                    "rightOperand": purpose,
                },
            }
        ],
    }
