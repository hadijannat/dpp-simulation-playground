from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008_compliance_versions"
down_revision = "007_digital_twin"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "compliance_rule_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("regulation", sa.String(120), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("rules", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("regulation", "version"),
    )

    op.create_table(
        "compliance_run_fixes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("compliance_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("value", postgresql.JSONB, server_default=sa.text("'null'::jsonb")),
        sa.Column("applied_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("compliance_run_fixes")
    op.drop_table("compliance_rule_versions")
