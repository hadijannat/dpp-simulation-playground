from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_add_collaboration"
down_revision = "002_add_gamification"
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    op.drop_table("annotations")
