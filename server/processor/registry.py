from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from converters import (
    compress_pdf,
    docx_to_markdown,
    docx_to_pdf,
    images_to_pdf,
    markdown_to_pdf,
    pdf_to_markdown,
    pdf_to_text,
    pptx_to_pdf,
    txt_to_markdown,
    xlsx_to_pdf,
)
from converters.base import ConversionContext, ConversionResult
from core.models.enums import ConversionOperation

Converter = Callable[[Path, ConversionContext], ConversionResult]

CONVERTERS: dict[ConversionOperation, Converter] = {
    ConversionOperation.DOCX_TO_PDF: docx_to_pdf.convert,
    ConversionOperation.PPTX_TO_PDF: pptx_to_pdf.convert,
    ConversionOperation.XLSX_TO_PDF: xlsx_to_pdf.convert,
    ConversionOperation.IMAGES_TO_PDF: images_to_pdf.convert,
    ConversionOperation.MARKDOWN_TO_PDF: markdown_to_pdf.convert,
    ConversionOperation.PDF_TO_MARKDOWN: pdf_to_markdown.convert,
    ConversionOperation.PDF_TO_TEXT: pdf_to_text.convert,
    ConversionOperation.COMPRESS_PDF: compress_pdf.convert,
    ConversionOperation.DOCX_TO_MARKDOWN: docx_to_markdown.convert,
    ConversionOperation.TXT_TO_MARKDOWN: txt_to_markdown.convert,
}


def get_converter(operation: ConversionOperation) -> Converter:
    return CONVERTERS[operation]
