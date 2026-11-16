from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from converters import (
    docx_to_pdf,
    images_to_pdf,
    markdown_to_pdf,
    pdf_to_markdown,
    txt_to_markdown,
)
from converters.base import ConversionContext, ConversionResult
from core.models.enums import ConversionOperation

Converter = Callable[[Path, ConversionContext], ConversionResult]

CONVERTERS: dict[ConversionOperation, Converter] = {
    ConversionOperation.DOCX_TO_PDF: docx_to_pdf.convert,
    ConversionOperation.PDF_TO_MARKDOWN: pdf_to_markdown.convert,
    ConversionOperation.TXT_TO_MARKDOWN: txt_to_markdown.convert,
    ConversionOperation.MARKDOWN_TO_PDF: markdown_to_pdf.convert,
    ConversionOperation.IMAGES_TO_PDF: images_to_pdf.convert,
}


def get_converter(operation: ConversionOperation) -> Converter:
    return CONVERTERS[operation]
