from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "011_journey_links"
down_revision = "010_journey_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("simulation_sessions", sa.Column("journey_run_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_simulation_sessions_journey_run",
        "simulation_sessions",
        "journey_runs",
        ["journey_run_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_simulation_sessions_journey_run", "simulation_sessions", type_="foreignkey")
    op.drop_column("simulation_sessions", "journey_run_id")
