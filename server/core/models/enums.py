from __future__ import annotations

from enum import StrEnum


class ConversionOperation(StrEnum):
    DOCX_TO_PDF = "docx_to_pdf"
    PDF_TO_MARKDOWN = "pdf_to_markdown"
    TXT_TO_MARKDOWN = "txt_to_markdown"
    MARKDOWN_TO_PDF = "markdown_to_pdf"
    IMAGES_TO_PDF = "images_to_pdf"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED}
