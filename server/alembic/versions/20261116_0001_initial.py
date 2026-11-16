"""Initial users, sessions, and conversion jobs.

Revision ID: 20261116_0001
Revises:
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from core.config import settings

revision: str = "20261116_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = settings.db_schema or "public"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True, schema=SCHEMA)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], schema=SCHEMA)
    op.create_index(
        "ix_sessions_token_hash", "sessions", ["token_hash"], unique=True, schema=SCHEMA
    )

    op.create_table(
        "conversion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(length=40), nullable=False),
        sa.Column("original_filename", sa.String(length=200), nullable=False),
        sa.Column("input_key", sa.String(length=500), nullable=False),
        sa.Column("output_key", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("output_size", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=160), nullable=False),
        sa.Column("upload_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_conversion_jobs_owner_id", "conversion_jobs", ["owner_id"], schema=SCHEMA)
    op.create_index("ix_conversion_jobs_status", "conversion_jobs", ["status"], schema=SCHEMA)
    op.create_index(
        "ix_conversion_jobs_created_at", "conversion_jobs", ["created_at"], schema=SCHEMA
    )
    op.create_index(
        "ix_conversion_jobs_expires_at", "conversion_jobs", ["expires_at"], schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_table("conversion_jobs", schema=SCHEMA)
    op.drop_table("sessions", schema=SCHEMA)
    op.drop_table("users", schema=SCHEMA)
