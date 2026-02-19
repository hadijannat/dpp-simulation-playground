from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009_ux_feedback"
down_revision = "008_compliance_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ux_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("journey_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journey_runs.id", ondelete="SET NULL")),
        sa.Column("locale", sa.String(10), server_default="en"),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("flow", sa.String(120), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("ux_feedback")
