from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_add_gamification"
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


def downgrade():
    op.drop_table("user_points")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
