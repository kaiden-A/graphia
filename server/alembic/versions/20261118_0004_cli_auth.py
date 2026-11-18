"""Add CLI browser-approval requests and session labels.

Revision ID: 20261118_0004
Revises: 20261117_0003
Create Date: 2026-11-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from core.config import settings

revision: str = "20261118_0004"
down_revision: str | None = "20261117_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = settings.db_schema or "public"


def upgrade() -> None:
    op.create_table(
        "cli_auth_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("challenge", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("denied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_cli_auth_requests_code_hash",
        "cli_auth_requests",
        ["code_hash"],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "ix_cli_auth_requests_user_id",
        "cli_auth_requests",
        ["user_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_cli_auth_requests_expires_at",
        "cli_auth_requests",
        ["expires_at"],
        schema=SCHEMA,
    )

    op.add_column(
        "sessions",
        sa.Column(
            "client",
            sa.String(length=16),
            nullable=False,
            server_default="web",
        ),
        schema=SCHEMA,
    )
    op.add_column(
        "sessions",
        sa.Column("label", sa.String(length=64), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("sessions", "label", schema=SCHEMA)
    op.drop_column("sessions", "client", schema=SCHEMA)
    op.drop_table("cli_auth_requests", schema=SCHEMA)
