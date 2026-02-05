import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dpp:dpp@postgres:5432/dpp_playground")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
COMPLIANCE_URL = os.getenv("COMPLIANCE_URL", "http://compliance-service:8002")
EDC_URL = os.getenv("EDC_URL", "http://edc-simulator:8004")
BASYX_BASE_URL = os.getenv("BASYX_BASE_URL", "http://aas-environment:8081")
BASYX_API_PREFIX = os.getenv("BASYX_API_PREFIX", "/api/v3.0")
AAS_REGISTRY_URL = os.getenv("AAS_REGISTRY_URL", "")
SUBMODEL_REGISTRY_URL = os.getenv("SUBMODEL_REGISTRY_URL", "")
