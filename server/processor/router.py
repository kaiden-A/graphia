from __future__ import annotations

import hmac
import logging
import uuid

from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.errors import AppError
from core.models.conversion_job import ConversionJob
from core.models.enums import JobStatus
from core.utils import utcnow
from processor.runner import run_job

logger = logging.getLogger(__name__)
router = APIRouter(tags=["internal"])


class ProcessRequest(BaseModel):
    jobId: uuid.UUID


class ProcessAccepted(BaseModel):
    status: str
    jobId: uuid.UUID | None = None
    jobStatus: str | None = None


def require_internal_token(
    x_internal_token: str | None = Header(default=None),
) -> None:
    provided = x_internal_token or ""
    if not hmac.compare_digest(provided, settings.internal_token):
        raise AppError(401, "Unauthorized.")


@router.post(
    "/internal/process",
    response_model=ProcessAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_internal_token)],
)
def process(
    payload: ProcessRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ProcessAccepted:
    job = db.get(ConversionJob, payload.jobId)
    if job is None:
        raise AppError(404, "Conversion not found.")
    if job.status is not JobStatus.PENDING:
        return ProcessAccepted(status="ignored", jobStatus=job.status.value)
    if job.upload_completed_at is None:
        raise AppError(409, "The upload is not complete.")

    claimed = db.execute(
        update(ConversionJob)
        .where(
            ConversionJob.id == payload.jobId,
            ConversionJob.status == JobStatus.PENDING,
            ConversionJob.upload_completed_at.is_not(None),
        )
        .values(
            status=JobStatus.PROCESSING,
            started_at=utcnow(),
            attempts=ConversionJob.attempts + 1,
        )
        .returning(ConversionJob.id)
    ).scalar_one_or_none()
    db.commit()

    if claimed is None:
        current = db.get(ConversionJob, payload.jobId)
        return ProcessAccepted(
            status="ignored",
            jobStatus=current.status.value if current else None,
        )

    executor = getattr(request.app.state, "executor", None)
    if executor is None:
        db.execute(
            update(ConversionJob)
            .where(ConversionJob.id == payload.jobId, ConversionJob.status == JobStatus.PROCESSING)
            .values(
                status=JobStatus.PENDING,
                started_at=None,
                attempts=ConversionJob.attempts - 1,
            )
        )
        db.commit()
        raise AppError(503, "The processor is not ready.")

    try:
        executor.submit(run_job, payload.jobId)
    except RuntimeError as exc:
        db.execute(
            update(ConversionJob)
            .where(ConversionJob.id == payload.jobId, ConversionJob.status == JobStatus.PROCESSING)
            .values(
                status=JobStatus.PENDING,
                started_at=None,
                attempts=ConversionJob.attempts - 1,
            )
        )
        db.commit()
        raise AppError(503, "The processor is shutting down.") from exc

    return ProcessAccepted(status="accepted", jobId=payload.jobId)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "processor"}
