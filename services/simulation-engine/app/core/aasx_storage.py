from __future__ import annotations

import base64
import binascii
import io
import os
import re
from uuid import uuid4
from sqlalchemy.orm import Session

from ..config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    MINIO_SECURE,
    MINIO_PUBLIC_URL,
    AASX_STORAGE_DIR,
)
from ..models.dpp_instance import DppInstance

try:
    from minio import Minio
except Exception:  # pragma: no cover - optional dependency
    Minio = None  # type: ignore


def _ensure_bucket(client: "Minio", bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]")


def _sanitize_filename(filename: str) -> str:
    candidate = (filename or "").replace("\\", "/")
    base = os.path.basename(candidate).strip().lstrip(".")
    if not base:
        base = "upload.aasx"
    sanitized = _SAFE_FILENAME.sub("_", base)
    return sanitized[:180]


def _store_local(filename: str, raw: bytes) -> dict:
    os.makedirs(AASX_STORAGE_DIR, exist_ok=True)
    key = f"{uuid4()}.aasx"
    path = os.path.join(AASX_STORAGE_DIR, key)
    with open(path, "wb") as handle:
        handle.write(raw)
    return {"storage": "local", "object_key": key, "path": path, "url": None}


def _store_minio(filename: str, raw: bytes) -> dict | None:
    if Minio is None:
        return None
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )
    _ensure_bucket(client, MINIO_BUCKET)
    safe_name = _sanitize_filename(filename)
    object_key = f"aasx/{uuid4()}/{safe_name}"
    client.put_object(
        MINIO_BUCKET,
        object_key,
        io.BytesIO(raw),
        length=len(raw),
        content_type="application/octet-stream",
    )
    public_url = None
    if MINIO_PUBLIC_URL:
        public_url = f"{MINIO_PUBLIC_URL.rstrip('/')}/{MINIO_BUCKET}/{object_key}"
    return {
        "storage": "minio",
        "object_key": object_key,
        "bucket": MINIO_BUCKET,
        "url": public_url,
    }


def store_aasx_payload(
    db: Session,
    session_id: str | None,
    filename: str,
    content_base64: str,
    metadata: dict,
) -> dict:
    safe_filename = _sanitize_filename(filename)
    try:
        raw = base64.b64decode(content_base64)
    except binascii.Error:
        raw = content_base64.encode("utf-8")
    try:
        stored = _store_minio(safe_filename, raw) or _store_local(safe_filename, raw)
    except Exception:
        stored = _store_local(safe_filename, raw)
    if session_id:
        instance = (
            db.query(DppInstance)
            .filter(DppInstance.session_id == session_id)
            .order_by(DppInstance.created_at.desc())
            .first()
        )
        if instance:
            instance.aasx_object_key = stored.get("object_key")
            instance.aasx_url = stored.get("url")
            instance.aasx_filename = safe_filename
            instance.compliance_status = {
                **(instance.compliance_status or {}),
                "aasx_metadata": metadata or {},
            }
            try:
                db.commit()
            except Exception:
                db.rollback()
    return stored
