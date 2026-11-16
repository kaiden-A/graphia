from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from core.models.conversion_job import ConversionJob
from core.models.enums import ConversionOperation, JobStatus
from core.operations import OperationSpec, get_spec, output_filename
from core.utils import ensure_utc, to_ms, utcnow


class CreateConversionIn(BaseModel):
    operation: ConversionOperation
    originalFilename: str = Field(min_length=1, max_length=255)
    fileSize: int = Field(gt=0)
    contentType: str = Field(default="", max_length=160)


class UploadTicket(BaseModel):
    url: str
    method: str = "PUT"
    headers: dict[str, str]
    expiresAt: int


class ConversionPublic(BaseModel):
    id: uuid.UUID
    operation: ConversionOperation
    operationLabel: str
    originalFilename: str
    status: JobStatus
    errorMessage: str | None
    fileSize: int
    outputSize: int | None
    outputFilename: str | None
    uploadCompleted: bool
    downloadAvailable: bool
    attempts: int
    createdAt: int | None
    startedAt: int | None
    completedAt: int | None
    expiresAt: int | None

    @classmethod
    def from_job(cls, job: ConversionJob) -> "ConversionPublic":
        expires_at = ensure_utc(job.expires_at)
        completed = job.status is JobStatus.COMPLETED
        not_expired = bool(expires_at and expires_at > utcnow())
        return cls(
            id=job.id,
            operation=job.operation,
            operationLabel=get_spec(job.operation).label,
            originalFilename=job.original_filename,
            status=job.status,
            errorMessage=job.error_message,
            fileSize=job.file_size,
            outputSize=job.output_size,
            outputFilename=(
                output_filename(job.original_filename, job.operation)
                if job.output_key
                else None
            ),
            uploadCompleted=job.upload_completed_at is not None,
            downloadAvailable=completed and not_expired,
            attempts=job.attempts,
            createdAt=to_ms(job.created_at),
            startedAt=to_ms(job.started_at),
            completedAt=to_ms(job.completed_at),
            expiresAt=to_ms(job.expires_at),
        )


class CreateConversionOut(BaseModel):
    job: ConversionPublic
    upload: UploadTicket


class DownloadOut(BaseModel):
    url: str
    expiresAt: int


class OperationOut(BaseModel):
    id: ConversionOperation
    label: str
    description: str
    inputExtensions: list[str]
    outputExtension: str

    @classmethod
    def from_spec(cls, spec: OperationSpec) -> "OperationOut":
        return cls(
            id=spec.id,
            label=spec.label,
            description=spec.description,
            inputExtensions=list(spec.input_extensions),
            outputExtension=spec.output_extension,
        )
