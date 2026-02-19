import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dpp:dpp@postgres:5432/dpp_playground")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
COMPLIANCE_URL = os.getenv("COMPLIANCE_URL", "http://compliance-service:8002")
EDC_URL = os.getenv("EDC_URL", "http://edc-simulator:8004")
AAS_ADAPTER_URL = os.getenv("AAS_ADAPTER_URL", "http://aas-adapter:8008")
BASYX_BASE_URL = os.getenv("BASYX_BASE_URL", "http://aas-environment:8081")
BASYX_API_PREFIX = os.getenv("BASYX_API_PREFIX", "/api/v3.0")
AAS_REGISTRY_URL = os.getenv("AAS_REGISTRY_URL", "")
SUBMODEL_REGISTRY_URL = os.getenv("SUBMODEL_REGISTRY_URL", "")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "dpp-aasx")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() in ("1", "true", "yes")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9100")
AASX_STORAGE_DIR = os.getenv("AASX_STORAGE_DIR", "data/aasx")


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


EVENT_STREAM_MAXLEN = _as_int("EVENT_STREAM_MAXLEN", 50000)
