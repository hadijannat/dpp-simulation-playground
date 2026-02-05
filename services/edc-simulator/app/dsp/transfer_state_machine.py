STATES = [
    "INITIAL",
    "PROVISIONING",
    "PROVISIONED",
    "REQUESTING",
    "REQUESTED",
    "STARTED",
    "COMPLETED",
    "TERMINATED",
]

TRANSITIONS = {
    "INITIAL": ["PROVISIONING"],
    "PROVISIONING": ["PROVISIONED", "TERMINATED"],
    "PROVISIONED": ["REQUESTING"],
    "REQUESTING": ["REQUESTED", "TERMINATED"],
    "REQUESTED": ["STARTED", "TERMINATED"],
    "STARTED": ["COMPLETED", "TERMINATED"],
}


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, [])
