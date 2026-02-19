from alembic import op
import sqlalchemy as sa

revision = "013_add_point_rules"
down_revision = "012_backfill_state"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "point_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_point_rules_event_type", "point_rules", ["event_type"], unique=True)


def downgrade():
    op.drop_index("ix_point_rules_event_type", table_name="point_rules")
    op.drop_table("point_rules")
