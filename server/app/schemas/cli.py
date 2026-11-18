from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.auth import UserPublic

CliAuthStatus = Literal["pending", "approved", "denied", "claimed", "expired"]


class CliAuthRequestIn(BaseModel):
    name: str = Field(default="Graphia CLI", min_length=1, max_length=64)
    challenge: str = Field(
        min_length=43,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Base64url SHA-256 of the CLI verifier.",
    )


class CliAuthRequestOut(BaseModel):
    code: str
    loginUrl: str
    expiresAt: int


class CliAuthStatusOut(BaseModel):
    name: str
    status: CliAuthStatus
    expiresAt: int


class CliTokenIn(BaseModel):
    code: str = Field(min_length=16, max_length=128)
    verifier: str = Field(min_length=16, max_length=256)


class CliTokenOut(BaseModel):
    token: str
    expiresAt: int
    user: UserPublic


class CliPendingOut(BaseModel):
    status: Literal["pending"] = "pending"


class CliLogoutOut(BaseModel):
    status: Literal["signed_out"] = "signed_out"
