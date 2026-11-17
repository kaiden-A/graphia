from __future__ import annotations

import logging
import uuid

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def trigger(job_id: uuid.UUID) -> tuple[bool, str | None]:
    """Ask Service B to accept a job. This waits only for the 202 handshake."""
    url = f"{settings.processor_url.rstrip('/')}/internal/process"
    try:
        # Cloud Run scales to zero, so the first trigger after idle waits for a
        # cold start (LibreOffice image, ~10s). The request returns as soon as
        # the processor accepts the job; it does not wait for the conversion.
        with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = client.post(
                url,
                json={"jobId": str(job_id)},
                headers={"X-Internal-Token": settings.internal_token},
            )
    except httpx.HTTPError:
        logger.exception("Could not reach the processor", extra={"job_id": str(job_id)})
        return False, "The conversion service is unavailable. Please try again."

    if response.status_code in {200, 202}:
        return True, None

    logger.warning(
        "Processor rejected trigger",
        extra={"job_id": str(job_id), "status_code": response.status_code},
    )
    if response.status_code == 409:
        return False, "The upload was not complete. Please upload the file again."
    return False, "The conversion service could not accept this job. Please try again."
