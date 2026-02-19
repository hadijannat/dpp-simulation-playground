from alembic import op
import sqlalchemy as sa

revision = "014_add_event_logs"
down_revision = "013_add_point_rules"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("user_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("source_service", sa.String(length=80), nullable=False),
        sa.Column("version", sa.String(length=16), nullable=False, server_default="1"),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("run_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stream", sa.String(length=120), nullable=False, server_default="simulation.events"),
        sa.Column("stream_message_id", sa.String(length=64), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("publish_error", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_event_logs_event_id", "event_logs", ["event_id"], unique=True)
    op.create_index("ix_event_logs_event_type", "event_logs", ["event_type"], unique=False)
    op.create_index("ix_event_logs_source_service", "event_logs", ["source_service"], unique=False)
    op.create_index("ix_event_logs_session_ts", "event_logs", ["session_id", "event_timestamp"], unique=False)
    op.create_index("ix_event_logs_run_ts", "event_logs", ["run_id", "event_timestamp"], unique=False)
    op.create_index("ix_event_logs_request_id", "event_logs", ["request_id"], unique=False)


def downgrade():
    op.drop_index("ix_event_logs_request_id", table_name="event_logs")
    op.drop_index("ix_event_logs_run_ts", table_name="event_logs")
    op.drop_index("ix_event_logs_session_ts", table_name="event_logs")
    op.drop_index("ix_event_logs_source_service", table_name="event_logs")
    op.drop_index("ix_event_logs_event_type", table_name="event_logs")
    op.drop_index("ix_event_logs_event_id", table_name="event_logs")
    op.drop_table("event_logs")
