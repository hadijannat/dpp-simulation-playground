from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_journey_runtime"
down_revision = "005_feature_expansion"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "journey_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(80), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("target_role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "journey_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_templates.id", ondelete="CASCADE")),
        sa.Column("step_key", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False),
        sa.Column("help_text", sa.Text),
        sa.Column("default_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("template_id", "step_key"),
        sa.UniqueConstraint("template_id", "order_index"),
    )

    op.create_table(
        "journey_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_templates.id")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("active_role", sa.String(50), nullable=False),
        sa.Column("locale", sa.String(10), server_default="en"),
        sa.Column("status", sa.String(30), server_default="active"),
        sa.Column("current_step_key", sa.String(120)),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id", ondelete="SET NULL")),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "journey_step_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("journey_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_key", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), server_default="completed"),
        sa.Column("payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("journey_step_runs")
    op.drop_table("journey_runs")
    op.drop_table("journey_steps")
    op.drop_table("journey_templates")
