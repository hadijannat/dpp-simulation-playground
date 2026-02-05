from alembic import op
import sqlalchemy as sa

revision = "012_backfill_state"
down_revision = "011_journey_links"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "migration_backfill_state",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), unique=True, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("migration_backfill_state")
