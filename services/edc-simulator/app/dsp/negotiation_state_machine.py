STATES = [
    "INITIAL",
    "REQUESTING",
    "REQUESTED",
    "OFFERED",
    "ACCEPTED",
    "AGREED",
    "VERIFIED",
    "FINALIZED",
    "TERMINATED",
]

TRANSITIONS = {
    "INITIAL": ["REQUESTING"],
    "REQUESTING": ["REQUESTED", "TERMINATED"],
    "REQUESTED": ["OFFERED", "TERMINATED"],
    "OFFERED": ["ACCEPTED", "TERMINATED"],
    "ACCEPTED": ["AGREED"],
    "AGREED": ["VERIFIED"],
    "VERIFIED": ["FINALIZED"],
}


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, [])
