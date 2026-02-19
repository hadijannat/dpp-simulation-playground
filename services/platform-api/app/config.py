import os

SIMULATION_URL = os.getenv("SIMULATION_URL", "http://simulation-engine:8001")
COMPLIANCE_URL = os.getenv("COMPLIANCE_URL", "http://compliance-service:8002")
GAMIFICATION_URL = os.getenv("GAMIFICATION_URL", "http://gamification-service:8003")
EDC_URL = os.getenv("EDC_URL", "http://edc-simulator:8004")
COLLABORATION_URL = os.getenv("COLLABORATION_URL", "http://collaboration-service:8005")
AAS_ADAPTER_URL = os.getenv("AAS_ADAPTER_URL", "http://aas-adapter:8008")
PLATFORM_CORE_URL = os.getenv("PLATFORM_CORE_URL", "http://platform-core:8007")


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Security hardening:
# In production this should stay false so upstream identity cannot be spoofed
# through dev headers when Authorization is absent.
ALLOW_DEV_HEADERS = _as_bool(os.getenv("ALLOW_DEV_HEADERS"), default=False)
