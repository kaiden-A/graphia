from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.models.user import User
from core.utils import to_ms


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=120)
    inviteCode: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


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


class AuthConfig(BaseModel):
    signupEnabled: bool
    signupRequiresCode: bool
