#!/usr/bin/env python3
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dpp:dpp@localhost:5432/dpp_playground")
BACKFILL_NAME = "journey_backfill_v1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_template(conn) -> str:
    row = conn.execute(
        text("SELECT id FROM journey_templates WHERE code = :code"),
        {"code": "manufacturer-core-e2e"},
    ).first()
    if row:
        return str(row[0])

    template_id = str(uuid.uuid4())
    conn.execute(
        text(
            """
            INSERT INTO journey_templates (id, code, name, description, target_role, is_active, created_at)
            VALUES (:id, :code, :name, :description, :target_role, true, :created_at)
            """
        ),
        {
            "id": template_id,
            "code": "manufacturer-core-e2e",
            "name": "Manufacturer Core E2E",
            "description": "Backfilled template for existing simulation sessions",
            "target_role": "manufacturer",
            "created_at": utc_now(),
        },
    )
    return template_id


def already_done(conn) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM migration_backfill_state WHERE name = :name"),
        {"name": BACKFILL_NAME},
    ).first()
    return row is not None


def mark_done(conn) -> None:
    conn.execute(
        text("INSERT INTO migration_backfill_state (name, completed_at) VALUES (:name, :completed_at)"),
        {"name": BACKFILL_NAME, "completed_at": utc_now()},
    )


MANUFACTURER_STEPS = [
    {
        "step_key": "create-dpp",
        "title": "Create Digital Product Passport",
        "action": "aas.create",
        "order_index": 0,
        "help_text": "Create an Asset Administration Shell for your product.",
        "default_payload": '{"id": "urn:dpp:asset-001", "product_name": "EV Battery Module", "product_category": "battery"}',
    },
    {
        "step_key": "add-submodel",
        "title": "Add Technical Data Submodel",
        "action": "aas.submodel.add",
        "order_index": 1,
        "help_text": "Add the technical specifications submodel to the DPP.",
        "default_payload": '{"submodel": {"idShort": "TechnicalData", "id": "urn:dpp:submodel:technical-data"}}',
    },
    {
        "step_key": "compliance-check",
        "title": "Run Compliance Check",
        "action": "compliance.check",
        "order_index": 2,
        "help_text": "Validate your DPP against ESPR, Battery Regulation, WEEE, and RoHS.",
        "default_payload": '{"regulations": ["ESPR", "Battery Regulation", "WEEE", "RoHS"]}',
    },
    {
        "step_key": "negotiate-transfer",
        "title": "Negotiate Data Transfer",
        "action": "edc.negotiate",
        "order_index": 3,
        "help_text": "Initiate a dataspace negotiation for your DPP data.",
        "default_payload": '{"asset_id": "urn:dpp:asset-001", "consumer_id": "BPNL000000000001", "provider_id": "BPNL000000000002"}',
    },
    {
        "step_key": "execute-transfer",
        "title": "Execute Data Transfer",
        "action": "edc.transfer",
        "order_index": 4,
        "help_text": "Complete the data transfer through the Eclipse Data Connector.",
        "default_payload": '{"asset_id": "urn:dpp:asset-001", "consumer_id": "BPNL000000000001", "provider_id": "BPNL000000000002"}',
    },
]


def ensure_steps(conn, template_id: str) -> None:
    existing = conn.execute(
        text("SELECT step_key FROM journey_steps WHERE template_id = :template_id"),
        {"template_id": template_id},
    ).fetchall()
    existing_keys = {row[0] for row in existing}

    for step in MANUFACTURER_STEPS:
        if step["step_key"] in existing_keys:
            continue
        conn.execute(
            text(
                """
                INSERT INTO journey_steps (id, template_id, step_key, title, action, order_index, help_text, default_payload)
                VALUES (:id, :template_id, :step_key, :title, :action, :order_index, :help_text, :default_payload::jsonb)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "template_id": template_id,
                "step_key": step["step_key"],
                "title": step["title"],
                "action": step["action"],
                "order_index": step["order_index"],
                "help_text": step["help_text"],
                "default_payload": step["default_payload"],
            },
        )


def backfill() -> None:
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        if already_done(conn):
            print("Backfill already applied; skipping.")
            return

        template_id = ensure_template(conn)
        ensure_steps(conn, template_id)
        sessions = conn.execute(
            text(
                """
                SELECT id, user_id, active_role, started_at, last_activity
                FROM simulation_sessions
                ORDER BY started_at ASC
                """
            )
        ).fetchall()

        for session in sessions:
            existing = conn.execute(
                text("SELECT id FROM journey_runs WHERE session_id = :session_id"),
                {"session_id": session.id},
            ).first()
            if existing:
                continue

            run_id = str(uuid.uuid4())
            conn.execute(
                text(
                    """
                    INSERT INTO journey_runs (
                        id, template_id, user_id, active_role, locale, status, current_step_key,
                        session_id, metadata, started_at, updated_at
                    ) VALUES (
                        :id, :template_id, :user_id, :active_role, :locale, :status, :current_step_key,
                        :session_id, :metadata, :started_at, :updated_at
                    )
                    """
                ),
                {
                    "id": run_id,
                    "template_id": template_id,
                    "user_id": session.user_id,
                    "active_role": session.active_role,
                    "locale": "en",
                    "status": "active",
                    "current_step_key": "backfilled",
                    "session_id": session.id,
                    "metadata": "{}",
                    "started_at": session.started_at or utc_now(),
                    "updated_at": session.last_activity or utc_now(),
                },
            )

            conn.execute(
                text("UPDATE simulation_sessions SET journey_run_id = :run_id WHERE id = :session_id"),
                {"run_id": run_id, "session_id": session.id},
            )

        mark_done(conn)

    print("Journey backfill completed.")


if __name__ == "__main__":
    backfill()
