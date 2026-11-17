from __future__ import annotations

import logging
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from converters.base import ConversionContext, ConversionError
from core.config import settings
from core.database import SessionLocal
from core.models.conversion_job import ConversionJob
from core.models.enums import ConversionOperation, JobStatus
from core.storage import Storage, get_storage
from core.utils import utcnow
from processor.registry import CONVERTERS, Converter
from processor.validation import validate_input

logger = logging.getLogger(__name__)
MAX_OUTPUT_BYTES = 200 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class JobSnapshot:
    """The job fields needed for a conversion, detached from its DB session."""

    id: uuid.UUID
    owner_id: uuid.UUID
    operation: ConversionOperation
    original_filename: str
    input_key: str
    attempts: int


def _load_job(job_id: uuid.UUID, session_factory: sessionmaker) -> JobSnapshot | None:
    db: Session = session_factory()
    try:
        job = db.get(ConversionJob, job_id)
        if job is None or job.status is not JobStatus.PROCESSING:
            return None
        return JobSnapshot(
            id=job.id,
            owner_id=job.owner_id,
            operation=job.operation,
            original_filename=job.original_filename,
            input_key=job.input_key,
            attempts=job.attempts,
        )
    finally:
        db.close()


def _mark_completed(
    job: JobSnapshot,
    output_key: str,
    output_size: int,
    session_factory: sessionmaker,
) -> bool:
    db: Session = session_factory()
    try:
        result = db.execute(
            update(ConversionJob)
            .where(
                ConversionJob.id == job.id,
                ConversionJob.status == JobStatus.PROCESSING,
                ConversionJob.attempts == job.attempts,
            )
            .values(
                status=JobStatus.COMPLETED,
                output_key=output_key,
                output_size=output_size,
                error_message=None,
                completed_at=utcnow(),
            )
        )
        db.commit()
        return result.rowcount > 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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
                completed_at=utcnow(),
            )
        )
        db.commit()
        if result.rowcount == 0:
            logger.warning(
                "Job was no longer PROCESSING when marking failure",
                extra={"job_id": str(job_id)},
            )
    except Exception:
        db.rollback()
        logger.exception(
            "Could not mark the job as failed; it may remain PROCESSING",
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

    # Do not hold a database connection while LibreOffice or another converter
    # runs. Neon can drop an idle connection, and a long conversion would then
    # fail when the job tries to record its result.
    job = _load_job(job_id, session_factory)
    if job is None:
        logger.info("Skipping job that is not PROCESSING", extra={"job_id": str(job_id)})
        return

    suffix = Path(job.original_filename).suffix.lower() or ".input"
    with tempfile.TemporaryDirectory(prefix=f"graphia-{job.id}-") as temp_dir:
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

            output_size = result.path.stat().st_size
            output_key = (
                f"conversions/{job.owner_id}/{job.id}/output/"
                f"attempt-{job.attempts}/result.{result.extension}"
            )
            storage.put_file(output_key, result.path, result.media_type)

            completed = _mark_completed(job, output_key, output_size, session_factory)
            if not completed:
                logger.warning(
                    "Job disappeared before completion; removing output",
                    extra={"job_id": str(job.id)},
                )
                storage.delete(output_key)

        except ConversionError as exc:
            logger.warning(
                "Conversion failed",
                extra={"job_id": str(job.id), "operation": job.operation.value},
            )
            _mark_failed(job.id, str(exc), session_factory, job.attempts)
        except Exception:
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
