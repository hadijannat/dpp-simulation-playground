import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dpp:dpp@postgres:5432/dpp_playground")
COMPLIANCE_URL = os.getenv("COMPLIANCE_URL", "http://compliance-service:8002")
