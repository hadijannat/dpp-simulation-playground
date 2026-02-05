from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_extend_schema"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("icon_url", sa.String(500)),
        sa.Column("points", sa.Integer, server_default="0"),
        sa.Column("rarity", sa.String(20), server_default="common"),
        sa.Column("criteria", postgresql.JSONB, nullable=False),
        sa.Column("category", sa.String(50)),
    )

    op.create_table(
        "user_achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("achievement_id", sa.Integer, sa.ForeignKey("achievements.id")),
        sa.Column("awarded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("context", postgresql.JSONB),
        sa.UniqueConstraint("user_id", "achievement_id"),
    )

    op.create_table(
        "user_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("total_points", sa.Integer, server_default="0"),
        sa.Column("current_streak_days", sa.Integer, server_default="0"),
        sa.Column("longest_streak_days", sa.Integer, server_default="0"),
        sa.Column("last_activity_date", sa.Date),
        sa.Column("level", sa.Integer, server_default="1"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("story_id", sa.Integer, sa.ForeignKey("user_stories.id")),
        sa.Column("target_element", sa.String(255)),
        sa.Column("annotation_type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("screenshot_url", sa.String(500)),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("votes_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("value", sa.Integer, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "target_id"),
    )

    op.create_table(
        "gap_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("story_id", sa.Integer, sa.ForeignKey("user_stories.id")),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "compliance_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id")),
        sa.Column("story_code", sa.String(30)),
        sa.Column("regulations", postgresql.JSONB),
        sa.Column("status", sa.String(30)),
        sa.Column("report", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "validation_results",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("result", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "edc_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_id", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "edc_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("policy_odrl", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("data_address", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("edc_assets")
    op.drop_table("edc_participants")
    op.drop_table("validation_results")
    op.drop_table("compliance_reports")
    op.drop_table("gap_reports")
    op.drop_table("votes")
    op.drop_table("comments")
    op.drop_table("annotations")
    op.drop_table("user_points")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
