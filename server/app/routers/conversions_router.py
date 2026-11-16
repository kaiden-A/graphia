from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies import client_ip, require_user
from app.schemas.conversion import (
    ConversionPublic,
    CreateConversionIn,
    CreateConversionOut,
    DownloadOut,
)
from app.services import conversion_services
from app.services.rate_limit import upload_limiter
from core.config import settings
from core.database import get_db
from core.errors import AppError
from core.models.user import User
from core.storage import get_storage

router = APIRouter(prefix="/api/conversions", tags=["conversions"])


@router.post("", response_model=CreateConversionOut, status_code=status.HTTP_201_CREATED)
def create_conversion(
    payload: CreateConversionIn,
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CreateConversionOut:
    if not upload_limiter.hit(
        f"upload:{client_ip(request)}",
        limit=settings.uploads_per_hour_per_ip,
        window_seconds=3600,
    ):
        raise AppError(429, "Too many uploads from this network. Try again later.")

    job, ticket = conversion_services.create_conversion(
        db,
        user=user,
        payload=payload,
        storage=get_storage(),
    )
    return CreateConversionOut(job=ConversionPublic.from_job(job), upload=ticket)


@router.post("/{job_id}/complete-upload", response_model=ConversionPublic)
def complete_upload(
    job_id: uuid.UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ConversionPublic:
    job = conversion_services.complete_upload(
        db,
        user=user,
        job_id=job_id,
        storage=get_storage(),
    )
    return ConversionPublic.from_job(job)


@router.get("/{job_id}", response_model=ConversionPublic)
def get_conversion(
    job_id: uuid.UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ConversionPublic:
    job = conversion_services.get_conversion(db, user=user, job_id=job_id)
    return ConversionPublic.from_job(job)


@router.get("/{job_id}/download", response_model=DownloadOut)
def download(
    job_id: uuid.UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DownloadOut:
    return conversion_services.get_download(
        db,
        user=user,
        job_id=job_id,
        storage=get_storage(),
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversion(
    job_id: uuid.UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Response:
    conversion_services.delete_conversion(
        db,
        user=user,
        job_id=job_id,
        storage=get_storage(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
