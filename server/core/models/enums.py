from __future__ import annotations

from enum import StrEnum


class ConversionOperation(StrEnum):
    DOCX_TO_PDF = "docx_to_pdf"
    PPTX_TO_PDF = "pptx_to_pdf"
    XLSX_TO_PDF = "xlsx_to_pdf"
    IMAGES_TO_PDF = "images_to_pdf"
    MARKDOWN_TO_PDF = "markdown_to_pdf"
    PDF_TO_MARKDOWN = "pdf_to_markdown"
    PDF_TO_TEXT = "pdf_to_text"
    COMPRESS_PDF = "compress_pdf"
    DOCX_TO_MARKDOWN = "docx_to_markdown"
    TXT_TO_MARKDOWN = "txt_to_markdown"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED}
