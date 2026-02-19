from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("keycloak_id", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("organization", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("role_type", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, default=False),
        sa.Column("preferences", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("user_id", "role_type"),
    )
    op.create_table(
        "epics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("story_count", sa.Integer, server_default="0"),
        sa.Column("order_index", sa.Integer),
        sa.Column("prerequisite_epics", postgresql.ARRAY(sa.Integer), server_default="{}"),
    )
    op.create_table(
        "user_stories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("epic_id", sa.Integer, sa.ForeignKey("epics.id")),
        sa.Column("code", sa.String(30), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("acceptance_criteria", postgresql.JSONB, nullable=False),
        sa.Column("difficulty_level", sa.String(20), server_default="intermediate"),
        sa.Column("estimated_duration_minutes", sa.Integer),
        sa.Column("applicable_roles", postgresql.ARRAY(sa.String(50)), server_default="{}"),
        sa.Column("order_index", sa.Integer),
    )
    op.create_table(
        "simulation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("active_role", sa.String(50), nullable=False),
        sa.Column("current_story_id", sa.Integer, sa.ForeignKey("user_stories.id")),
        sa.Column("session_state", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_activity", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean, default=True),
    )
    op.create_table(
        "story_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("story_id", sa.Integer, sa.ForeignKey("user_stories.id")),
        sa.Column("role_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), server_default="not_started"),
        sa.Column("completion_percentage", sa.Integer, server_default="0"),
        sa.Column("steps_completed", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("validation_results", postgresql.JSONB),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("time_spent_seconds", sa.Integer, server_default="0"),
        sa.UniqueConstraint("user_id", "story_id", "role_type"),
    )
    op.create_table(
        "dpp_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id")),
        sa.Column("aas_identifier", sa.String(500), nullable=False),
        sa.Column("product_identifier", sa.String(255)),
        sa.Column("product_name", sa.String(255)),
        sa.Column("product_category", sa.String(100)),
        sa.Column("compliance_status", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "edc_negotiations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id")),
        sa.Column("negotiation_id", sa.String(255), nullable=False),
        sa.Column("provider_participant_id", sa.String(255)),
        sa.Column("consumer_participant_id", sa.String(255)),
        sa.Column("asset_id", sa.String(255)),
        sa.Column("current_state", sa.String(30)),
        sa.Column("policy_odrl", postgresql.JSONB),
        sa.Column("state_history", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("edc_negotiations")
    op.drop_table("dpp_instances")
    op.drop_table("story_progress")
    op.drop_table("simulation_sessions")
    op.drop_table("user_stories")
    op.drop_table("epics")
    op.drop_table("user_roles")
    op.drop_table("users")
