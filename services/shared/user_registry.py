from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value[:limit]


def _extract_keycloak_id(token: dict | None) -> str | None:
    if not token:
        return None
    return (
        token.get("sub")
        or token.get("preferred_username")
        or token.get("username")
        or token.get("user_id")
    )


def resolve_user_id(db: Session, token: dict | None) -> Optional[str]:
    keycloak_id = _extract_keycloak_id(token)
    if not keycloak_id:
        return None
    keycloak_id = _truncate(str(keycloak_id), 255) or None
    if not keycloak_id:
        return None

    email = token.get("email") if token else None
    email = _truncate(email, 255) if email else None
    display_name = (
        (token.get("name") if token else None)
        or (token.get("preferred_username") if token else None)
        or email
        or keycloak_id
    )
    display_name = _truncate(display_name, 255) or keycloak_id

    row = db.execute(
        text("SELECT id FROM users WHERE keycloak_id = :kid"),
        {"kid": keycloak_id},
    ).first()
    if row:
        return str(row[0])

    if email:
        row = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).first()
        if row:
            db.execute(
                text("UPDATE users SET keycloak_id = :kid WHERE id = :id"),
                {"kid": keycloak_id, "id": row[0]},
            )
            db.commit()
            return str(row[0])

    user_id = uuid4()
    if not email:
        email = _truncate(f"{keycloak_id}@local", 255)
    try:
        db.execute(
            text(
                "INSERT INTO users (id, keycloak_id, email, display_name) "
                "VALUES (:id, :kid, :email, :display_name)"
            ),
            {
                "id": user_id,
                "kid": keycloak_id,
                "email": email,
                "display_name": display_name,
            },
        )
        db.commit()
        return str(user_id)
    except IntegrityError:
        db.rollback()
        row = db.execute(
            text("SELECT id FROM users WHERE keycloak_id = :kid"),
            {"kid": keycloak_id},
        ).first()
        if row:
            return str(row[0])
        if email:
            row = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).first()
            if row:
                return str(row[0])
        raise
