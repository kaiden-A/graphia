from __future__ import annotations

import logging
import uuid
from datetime import timedelta

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.schemas.conversion import CreateConversionIn, DownloadOut, UploadTicket
from app.services import processor_client
from core.config import settings
from core.errors import AppError
from core.models.conversion_job import ConversionJob
from core.models.enums import JobStatus
from core.models.user import User
from core.operations import output_filename, prefix_matches, validate_upload_metadata
from core.storage import Storage
from core.utils import ensure_utc, to_ms, utcnow

logger = logging.getLogger(__name__)


def _owned_job(db: Session, job_id: uuid.UUID, user: User) -> ConversionJob:
    job = db.execute(
        select(ConversionJob).where(
            ConversionJob.id == job_id,
            ConversionJob.owner_id == user.id,
        )
    ).scalar_one_or_none()
    if job is None:
        raise AppError(404, "Conversion not found.")
    return job


def _active_job_count(db: Session, user: User) -> int:
    # Unconfirmed uploads older than 30 minutes are abandoned; do not let them
    # block the user's next attempt. The cleanup script removes the rows later.
    recent_upload_cutoff = utcnow() - timedelta(minutes=30)
    return int(
        db.execute(
            select(func.count(ConversionJob.id)).where(
                ConversionJob.owner_id == user.id,
                ConversionJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]),
                or_(
                    ConversionJob.upload_completed_at.is_not(None),
                    ConversionJob.created_at >= recent_upload_cutoff,
                ),
            )
        ).scalar_one()
    )


def _jobs_today(db: Session) -> int:
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        db.execute(
            select(func.count(ConversionJob.id)).where(ConversionJob.created_at >= start)
        ).scalar_one()
    )


def create_conversion(
    db: Session,
    *,
    user: User,
    payload: CreateConversionIn,
    storage: Storage,
) -> tuple[ConversionJob, UploadTicket]:
    safe_name, ext, canonical_type = validate_upload_metadata(
        operation=payload.operation,
        filename=payload.originalFilename,
        file_size=payload.fileSize,
        content_type=payload.contentType,
        max_bytes=settings.max_upload_bytes,
    )

    if _jobs_today(db) >= settings.daily_job_limit:
        raise AppError(429, "The daily conversion limit has been reached. Try again tomorrow.")
    if _active_job_count(db, user) >= settings.max_active_jobs_per_user:
        raise AppError(
            429,
            f"You already have {settings.max_active_jobs_per_user} conversions in progress.",
        )

    job_id = uuid.uuid4()
    input_key = f"conversions/{user.id}/{job_id}/input/source.{ext}"
    now = utcnow()

    try:
        upload_url = storage.presign_put(
            input_key,
            canonical_type,
            settings.upload_url_ttl_seconds,
        )
    except Exception as exc:
        logger.exception("Could not create a presigned upload URL")
        raise AppError(503, "File storage is not available right now.") from exc

    job = ConversionJob(
        id=job_id,
        owner_id=user.id,
        operation=payload.operation,
        original_filename=safe_name,
        input_key=input_key,
        status=JobStatus.PENDING,
        file_size=payload.fileSize,
        content_type=canonical_type,
        expires_at=now + timedelta(hours=settings.job_expiry_hours),
        created_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    ticket = UploadTicket(
        url=upload_url,
        headers={"Content-Type": canonical_type},
        expiresAt=to_ms(now + timedelta(seconds=settings.upload_url_ttl_seconds)) or 0,
    )
    return job, ticket


def _mark_failed_if_pending(db: Session, job_id: uuid.UUID, message: str) -> None:
    db.execute(
        update(ConversionJob)
        .where(
            ConversionJob.id == job_id,
            ConversionJob.status == JobStatus.PENDING,
        )
        .values(
            status=JobStatus.FAILED,
            error_message=message[:1000],
            completed_at=utcnow(),
        )
    )
    db.commit()


def complete_upload(
    db: Session,
    *,
    user: User,
    job_id: uuid.UUID,
    storage: Storage,
) -> ConversionJob:
    job = _owned_job(db, job_id, user)

    if job.status in {JobStatus.PROCESSING, JobStatus.COMPLETED}:
        return job
    if job.status is JobStatus.FAILED:
        if job.attempts == 0 and job.upload_completed_at is not None:
            job.status = JobStatus.PENDING
            job.error_message = None
            db.commit()
        else:
            raise AppError(409, "This conversion failed. Start a new conversion.")

    if job.upload_completed_at is None:
        try:
            info = storage.head(job.input_key)
        except Exception as exc:
            logger.exception("Could not inspect uploaded object")
            raise AppError(503, "Could not verify the upload. Try again.") from exc
        if info is None:
            raise AppError(409, "The upload has not reached storage yet. Try again in a moment.")
        if info.size <= 0:
            storage.delete(job.input_key)
            _mark_failed_if_pending(db, job.id, "The uploaded file is empty.")
            raise AppError(422, "The uploaded file is empty.")
        if info.size > settings.max_upload_bytes:
            storage.delete(job.input_key)
            _mark_failed_if_pending(
                db,
                job.id,
                f"The file is larger than {settings.max_upload_mb} MB.",
            )
            raise AppError(413, f"The file is larger than {settings.max_upload_mb} MB.")

        if info.content_type:
            actual_type = info.content_type.split(";")[0].strip().lower()
            if actual_type and actual_type != job.content_type.split(";")[0].strip().lower():
                storage.delete(job.input_key)
                _mark_failed_if_pending(
                    db, job.id, "The uploaded file type does not match the conversion."
                )
                raise AppError(415, "The uploaded file type does not match the conversion.")

        end = min(info.size - 1, 4095)
        try:
            prefix = storage.read_range(job.input_key, 0, end)
        except Exception as exc:
            logger.exception("Could not inspect uploaded object")
            raise AppError(503, "Could not verify the upload. Try again.") from exc

        if not prefix_matches(job.operation, job.original_filename, prefix):
            storage.delete(job.input_key)
            _mark_failed_if_pending(
                db, job.id, "The uploaded file does not look like the selected format."
            )
            raise AppError(415, "The uploaded file does not look like the selected format.")

        job.file_size = info.size
        job.upload_completed_at = utcnow()
        db.commit()
        db.refresh(job)

    accepted, message = processor_client.trigger(job.id)
    if not accepted:
        _mark_failed_if_pending(
            db,
            job.id,
            message or "The conversion service could not accept this job.",
        )
        db.refresh(job)
    else:
        db.refresh(job)
    return job


def get_conversion(db: Session, *, user: User, job_id: uuid.UUID) -> ConversionJob:
    return _owned_job(db, job_id, user)


def get_download(db: Session, *, user: User, job_id: uuid.UUID, storage: Storage) -> DownloadOut:
    job = _owned_job(db, job_id, user)
    if job.status is not JobStatus.COMPLETED or not job.output_key:
        raise AppError(409, "This conversion is not ready yet.")
    expires_at = ensure_utc(job.expires_at)
    if expires_at is None or expires_at <= utcnow():
        raise AppError(410, "This file has expired. Upload it again to convert it.")

    filename = output_filename(job.original_filename, job.operation)
    try:
        url = storage.presign_get(job.output_key, filename, settings.download_url_ttl_seconds)
    except Exception as exc:
        logger.exception("Could not create a presigned download URL")
        raise AppError(503, "The download is not available right now.") from exc
    return DownloadOut(
        url=url,
        expiresAt=to_ms(utcnow() + timedelta(seconds=settings.download_url_ttl_seconds)) or 0,
    )


def delete_conversion(db: Session, *, user: User, job_id: uuid.UUID, storage: Storage) -> None:
    job = _owned_job(db, job_id, user)
    keys = [job.input_key]
    if job.output_key:
        keys.append(job.output_key)

    # Delete the row conditionally so a job that B claimed in the meantime is
    # not left with its input removed mid-conversion.
    result = db.execute(
        delete(ConversionJob).where(
            ConversionJob.id == job.id,
            ConversionJob.owner_id == user.id,
            ConversionJob.status != JobStatus.PROCESSING,
        )
    )
    if result.rowcount == 0:
        db.rollback()
        raise AppError(409, "This conversion is being processed and cannot be deleted yet.")
    db.commit()

    for key in keys:
        try:
            storage.delete(key)
        except Exception:
            logger.warning("Failed to delete storage object", extra={"key": key}, exc_info=True)


