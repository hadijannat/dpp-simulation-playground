import os
from jose import jwt


def decode_jwt(token: str) -> dict:
    secret = os.getenv("JWT_SECRET", "dev-secret")
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
    except Exception:
        return {}
