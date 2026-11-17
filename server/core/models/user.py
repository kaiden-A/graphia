from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base
from core.utils import utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("idp_issuer", "zitadel_sub", name="uq_users_idp_subject"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    idp_issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    zitadel_sub: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Kept nullable for the migration window; Zitadel is the only sign-in path.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    sessions: Mapped[list["UserSession"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["ConversionJob"]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )
