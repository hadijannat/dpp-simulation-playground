from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_digital_twin"
down_revision = "006_journey_runtime"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digital_twin_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dpp_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dpp_instances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "digital_twin_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("digital_twin_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_key", sa.String(120), nullable=False),
        sa.Column("node_type", sa.String(60), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("snapshot_id", "node_key"),
    )

    op.create_table(
        "digital_twin_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("digital_twin_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("edge_key", sa.String(120), nullable=False),
        sa.Column("source_node_key", sa.String(120), nullable=False),
        sa.Column("target_node_key", sa.String(120), nullable=False),
        sa.Column("label", sa.String(255)),
        sa.Column("payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("snapshot_id", "edge_key"),
    )


def downgrade():
    op.drop_table("digital_twin_edges")
    op.drop_table("digital_twin_nodes")
    op.drop_table("digital_twin_snapshots")
