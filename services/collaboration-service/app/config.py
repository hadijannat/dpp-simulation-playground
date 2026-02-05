import os

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./collaboration.db"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
