from __future__ import annotations

from pydantic import BaseModel


class AuthConfigOut(BaseModel):
    mode: str = "browser-approval"


class LimitsOut(BaseModel):
    maxUploadMb: int
    maxActiveJobs: int
    uploadsPerHour: int
    jobExpiryHours: int


class ConfigOut(BaseModel):
    appName: str
    version: str
    webUrl: str
    auth: AuthConfigOut
    limits: LimitsOut
