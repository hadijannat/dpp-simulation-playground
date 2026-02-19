from alembic import op

revision = "010_journey_indexes"
down_revision = "009_ux_feedback"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_journey_runs_user_id", "journey_runs", ["user_id"])
    op.create_index("ix_journey_runs_status", "journey_runs", ["status"])
    op.create_index("ix_journey_step_runs_run", "journey_step_runs", ["journey_run_id"])
    op.create_index("ix_ux_feedback_created_at", "ux_feedback", ["created_at"])


def downgrade():
    op.drop_index("ix_ux_feedback_created_at", table_name="ux_feedback")
    op.drop_index("ix_journey_step_runs_run", table_name="journey_step_runs")
    op.drop_index("ix_journey_runs_status", table_name="journey_runs")
    op.drop_index("ix_journey_runs_user_id", table_name="journey_runs")
