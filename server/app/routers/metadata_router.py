from __future__ import annotations

from fastapi import APIRouter

from app.schemas.config import AuthConfigOut, ConfigOut, LimitsOut
from app.schemas.conversion import OperationOut
from core.config import settings
from core.operations import OPERATIONS

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/operations", response_model=list[OperationOut])
def operations() -> list[OperationOut]:
    return [OperationOut.from_spec(spec) for spec in OPERATIONS.values()]


@router.get("/config", response_model=ConfigOut)
def config() -> ConfigOut:
    """Public CLI bootstrap. Never include secrets here."""
    return ConfigOut(
        appName=settings.app_name,
        version=settings.app_version,
        webUrl=settings.public_base_url.rstrip("/"),
        auth=AuthConfigOut(),
        limits=LimitsOut(
            maxUploadMb=settings.max_upload_mb,
            maxActiveJobs=settings.max_active_jobs_per_user,
            uploadsPerHour=settings.uploads_per_hour_per_member,
            jobExpiryHours=settings.job_expiry_hours,
        ),
    )
