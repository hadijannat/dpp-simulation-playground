from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_feature_expansion"
down_revision = "004_backend_alignment"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("dpp_instances", sa.Column("aasx_object_key", sa.String(500)))
    op.add_column("dpp_instances", sa.Column("aasx_url", sa.String(500)))
    op.add_column("dpp_instances", sa.Column("aasx_filename", sa.String(255)))

    op.add_column("gap_reports", sa.Column("votes_count", sa.Integer, server_default="0"))

    op.create_table(
        "edc_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transfer_id", sa.String(255), unique=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id")),
        sa.Column("asset_id", sa.String(255)),
        sa.Column("consumer_participant_id", sa.String(255)),
        sa.Column("provider_participant_id", sa.String(255)),
        sa.Column("current_state", sa.String(30)),
        sa.Column("state_history", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("edc_transfers")
    op.drop_column("gap_reports", "votes_count")
    op.drop_column("dpp_instances", "aasx_filename")
    op.drop_column("dpp_instances", "aasx_url")
    op.drop_column("dpp_instances", "aasx_object_key")
