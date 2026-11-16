from __future__ import annotations

import logging
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from converters.base import ConversionContext, ConversionError
from core.config import settings
from core.database import SessionLocal
from core.models.conversion_job import ConversionJob
from core.models.enums import JobStatus
from core.storage import Storage, get_storage
from core.utils import utcnow
from processor.registry import CONVERTERS, Converter
from processor.validation import validate_input

logger = logging.getLogger(__name__)
MAX_OUTPUT_BYTES = 200 * 1024 * 1024


def _mark_failed(
    job_id: uuid.UUID,
    message: str,
    session_factory: sessionmaker,
    attempts: int,
) -> None:
    db: Session = session_factory()
    try:
        result = db.execute(
            update(ConversionJob)
            .where(
                ConversionJob.id == job_id,
                ConversionJob.status == JobStatus.PROCESSING,
                ConversionJob.attempts == attempts,
            )
            .values(
                status=JobStatus.FAILED,
                error_message=message[:1000],
                completed_at=datetime.now(UTC),
            )
        )
        db.commit()
        if result.rowcount == 0:
            logger.warning(
                "Job was no longer PROCESSING when marking failure",
                extra={"job_id": str(job_id)},
            )
    finally:
        db.close()


def run_job(
    job_id: uuid.UUID,
    *,
    session_factory: sessionmaker = SessionLocal,
    storage: Storage | None = None,
    converters: dict | None = None,
) -> None:
    storage = storage or get_storage()
    converter_map = converters or CONVERTERS

    db: Session = session_factory()
    try:
        job = db.get(ConversionJob, job_id)
        if job is None or job.status is not JobStatus.PROCESSING:
            logger.info("Skipping job that is not PROCESSING", extra={"job_id": str(job_id)})
            return

        suffix = Path(job.original_filename).suffix.lower() or ".input"
        with tempfile.TemporaryDirectory(prefix=f"graphia-{job_id}-") as temp_dir:
            workdir = Path(temp_dir)
            input_path = workdir / f"input{suffix}"
            output_key: str | None = None

            try:
                storage.download_to(job.input_key, input_path)
                validate_input(job.operation, input_path)

                converter: Converter = converter_map[job.operation]
                context = ConversionContext(
                    workdir=workdir,
                    original_filename=job.original_filename,
                    timeout_seconds=settings.conversion_timeout_seconds,
                    soffice_bin=settings.soffice_bin,
                )
                result = converter(input_path, context)
                if not result.path.exists() or result.path.stat().st_size <= 0:
                    raise ConversionError("The conversion produced an empty file.")
                if result.path.stat().st_size > MAX_OUTPUT_BYTES:
                    raise ConversionError("The conversion produced a file that is too large.")

                output_key = (
                    f"conversions/{job.owner_id}/{job.id}/output/"
                    f"attempt-{job.attempts}/result.{result.extension}"
                )
                storage.put_file(output_key, result.path, result.media_type)

                completed = db.execute(
                    update(ConversionJob)
                    .where(
                        ConversionJob.id == job.id,
                        ConversionJob.status == JobStatus.PROCESSING,
                        ConversionJob.attempts == job.attempts,
                    )
                    .values(
                        status=JobStatus.COMPLETED,
                        output_key=output_key,
                        output_size=result.path.stat().st_size,
                        error_message=None,
                        completed_at=utcnow(),
                    )
                )
                db.commit()
                if completed.rowcount == 0:
                    logger.warning(
                        "Job disappeared before completion; removing output",
                        extra={"job_id": str(job.id)},
                    )
                    storage.delete(output_key)

            except ConversionError as exc:
                db.rollback()
                logger.warning(
                    "Conversion failed",
                    extra={"job_id": str(job.id), "operation": job.operation.value},
                )
                _mark_failed(job.id, str(exc), session_factory, job.attempts)
            except Exception:
                db.rollback()
                logger.exception(
                    "Unexpected conversion failure",
                    extra={"job_id": str(job.id), "operation": job.operation.value},
                )
                _mark_failed(
                    job.id,
                    "Conversion failed unexpectedly. Please try again.",
                    session_factory,
                    job.attempts,
                )
    finally:
        db.close()
