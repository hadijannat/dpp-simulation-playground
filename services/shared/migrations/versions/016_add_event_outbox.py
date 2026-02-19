from alembic import op
import sqlalchemy as sa

revision = "016_add_event_outbox"
down_revision = "015_add_audit_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("stream", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("stream_message_id", sa.String(length=64), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_event_outbox_event_id", "event_outbox", ["event_id"], unique=True)
    op.create_index("ix_event_outbox_stream", "event_outbox", ["stream"], unique=False)
    op.create_index("ix_event_outbox_status", "event_outbox", ["status"], unique=False)
    op.create_index("ix_event_outbox_available_at", "event_outbox", ["available_at"], unique=False)
    op.create_index("ix_event_outbox_locked_at", "event_outbox", ["locked_at"], unique=False)


def downgrade():
    op.drop_index("ix_event_outbox_locked_at", table_name="event_outbox")
    op.drop_index("ix_event_outbox_available_at", table_name="event_outbox")
    op.drop_index("ix_event_outbox_status", table_name="event_outbox")
    op.drop_index("ix_event_outbox_stream", table_name="event_outbox")
    op.drop_index("ix_event_outbox_event_id", table_name="event_outbox")
    op.drop_table("event_outbox")
