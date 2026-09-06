"""baseline schema (Telegram-based jobs + user_profiles)

Revision ID: 0001
Revises:
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

job_status = sa.Enum(
    "queued", "downloading", "transcribing", "translating", "analyzing",
    "planning_edits", "rendering", "generating_assets", "done", "failed", "cancelled",
    name="jobstatus",
)
creator_profile = sa.Enum("creator", "coach", "podcaster", "business", name="creatorprofile")


def upgrade() -> None:
    bind = op.get_bind()
    job_status.create(bind, checkfirst=True)
    creator_profile.create(bind, checkfirst=True)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("telegram_user_id", sa.String(32), nullable=False),
        sa.Column("telegram_chat_id", sa.String(32), nullable=False),
        sa.Column("telegram_message_id", sa.String(32), nullable=True),
        sa.Column("status", job_status, nullable=False, server_default="queued"),
        sa.Column("input_r2_key", sa.String(512), nullable=True),
        sa.Column("output_r2_key", sa.String(512), nullable=True),
        sa.Column("local_input_path", sa.String(512), nullable=True),
        sa.Column("local_output_path", sa.String(512), nullable=True),
        sa.Column("transcript", sa.JSON(), nullable=True),
        sa.Column("edit_plan", sa.JSON(), nullable=True),
        sa.Column("quality_report", sa.JSON(), nullable=True),
        sa.Column("caption_suggestions", sa.Text(), nullable=True),
        sa.Column("thumbnail_timestamps", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "user_profiles",
        sa.Column("telegram_user_id", sa.String(32), primary_key=True),
        sa.Column("profile", creator_profile, nullable=False, server_default="creator"),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("prefer_captions", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("prefer_subtitles", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("prefer_thumbnails", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.drop_table("jobs")
    bind = op.get_bind()
    creator_profile.drop(bind, checkfirst=True)
    job_status.drop(bind, checkfirst=True)
