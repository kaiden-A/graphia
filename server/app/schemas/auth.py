from __future__ import annotations

import uuid

from pydantic import BaseModel

from core.models.user import User
from core.utils import to_ms


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    createdAt: int | None

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=to_ms(user.created_at),
        )


class LogoutResponse(BaseModel):
    logoutUrl: str | None
