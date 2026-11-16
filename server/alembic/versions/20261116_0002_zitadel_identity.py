"""Add Zitadel identity fields.

Revision ID: 20261116_0002
Revises: 20261116_0001
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from core.config import settings

revision: str = "20261116_0002"
down_revision: str | None = "20261116_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = settings.db_schema or "public"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("idp_issuer", sa.String(length=255), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "users",
        sa.Column("zitadel_sub", sa.String(length=64), nullable=True),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_users_idp_subject",
        "users",
        ["idp_issuer", "zitadel_sub"],
        schema=SCHEMA,
    )
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            f"UPDATE {SCHEMA}.users SET password_hash = '' "
            "WHERE password_hash IS NULL"
        )
    )
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
        schema=SCHEMA,
    )
    op.drop_constraint("uq_users_idp_subject", "users", type_="unique", schema=SCHEMA)
    op.drop_column("users", "zitadel_sub", schema=SCHEMA)
    op.drop_column("users", "idp_issuer", schema=SCHEMA)
