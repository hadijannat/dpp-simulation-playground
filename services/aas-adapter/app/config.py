import os

BASYX_BASE_URL = os.getenv("BASYX_BASE_URL", "http://aas-environment:8081")
BASYX_API_PREFIX = os.getenv("BASYX_API_PREFIX", "/shells")
