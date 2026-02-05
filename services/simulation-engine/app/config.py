import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dpp:dpp@postgres:5432/dpp_playground")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
