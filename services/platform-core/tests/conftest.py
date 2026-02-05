from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from services.shared.models.base import Base  # noqa: E402
from services.shared.models.user import User  # noqa: E402, F401
from services.shared.models.session import SimulationSession  # noqa: E402, F401
from services.shared.models.story import UserStory  # noqa: E402, F401
from services.shared.models.dpp_instance import DppInstance  # noqa: E402, F401
from services.shared.models.journey_template import JourneyTemplate  # noqa: E402
from services.shared.models.journey_step import JourneyStep  # noqa: E402
from services.shared.models.journey_run import JourneyRun  # noqa: E402, F401
from services.shared.models.journey_step_run import JourneyStepRun  # noqa: E402, F401
from services.shared.models.digital_twin_snapshot import DigitalTwinSnapshot  # noqa: E402, F401
from services.shared.models.digital_twin_node import DigitalTwinNode  # noqa: E402, F401
from services.shared.models.digital_twin_edge import DigitalTwinEdge  # noqa: E402, F401
from services.shared.models.ux_feedback import UxFeedback  # noqa: E402, F401

from app.core.db import get_db  # noqa: E402
from app import main  # noqa: E402


SQLITE_URL = "sqlite://"

HEADERS = {
    "X-Dev-User": "test-user",
    "X-Dev-Roles": "developer,manufacturer,admin,regulator,consumer,recycler",
}


def _set_all_roles(request):
    """Dev-bypass auth that grants all roles."""
    request.state.user = {
        "sub": "test-user",
        "preferred_username": "test-user",
        "iss": "dev-bypass",
        "realm_access": {
            "roles": ["developer", "manufacturer", "admin", "regulator", "consumer", "recycler"]
        },
    }


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite database and yield a session.

    The engine uses ``StaticPool`` so every connection sees the same
    in-memory database. Foreign-key enforcement is turned on via a
    ``connect`` event listener.
    """
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create tables, skipping server_default expressions that use
    # PostgreSQL-specific syntax (e.g. ``'{}'::jsonb``).
    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        # Disable FK enforcement before DROP to avoid circular-dependency errors
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.commit()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session, monkeypatch):
    """Return a ``TestClient`` wired to the in-memory database.

    * Overrides ``get_db`` so all routes use the test session.
    * Monkeypatches ``verify_request`` to bypass auth and set dev roles.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    main.app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(main, "verify_request", _set_all_roles)

    yield TestClient(main.app)

    main.app.dependency_overrides.clear()


@pytest.fixture()
def seed_template(db_session):
    """Insert a journey template with two steps and return (template, steps)."""
    template_id = uuid4()
    template = JourneyTemplate(
        id=template_id,
        code="manufacturer-core-e2e",
        name="Manufacturer Core E2E",
        description="End-to-end manufacturer journey",
        target_role="manufacturer",
        is_active=True,
    )
    db_session.add(template)
    db_session.flush()  # ensure template row exists before FK-referencing steps

    step_1_id = uuid4()
    step_2_id = uuid4()
    step_1 = JourneyStep(
        id=step_1_id,
        template_id=template_id,
        step_key="create-product",
        title="Create Product",
        action="create_product",
        order_index=0,
        help_text="Create a new product",
        default_payload={},
    )
    step_2 = JourneyStep(
        id=step_2_id,
        template_id=template_id,
        step_key="submit-compliance",
        title="Submit Compliance",
        action="submit_compliance",
        order_index=1,
        help_text="Submit for compliance check",
        default_payload={},
    )
    db_session.add_all([step_1, step_2])
    db_session.commit()

    return template, [step_1, step_2]
