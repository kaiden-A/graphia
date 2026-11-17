from __future__ import annotations

import pytest

from app.schemas.conversion import OperationOut
from core.models.enums import ConversionOperation
from core.operations import (
    OPERATIONS,
    get_spec,
    output_filename,
    prefix_matches,
    validate_upload_metadata,
)
from processor.registry import CONVERTERS

SIGNATURES = [
    (ConversionOperation.DOCX_TO_PDF, "source.docx", b"PK\x03\x04"),
    (ConversionOperation.DOCX_TO_MARKDOWN, "source.docx", b"PK\x03\x04"),
    (ConversionOperation.PPTX_TO_PDF, "source.pptx", b"PK\x03\x04"),
    (ConversionOperation.XLSX_TO_PDF, "source.xlsx", b"PK\x03\x04"),
    (ConversionOperation.PDF_TO_MARKDOWN, "source.pdf", b"%PDF-"),
    (ConversionOperation.PDF_TO_TEXT, "source.pdf", b"%PDF-"),
    (ConversionOperation.COMPRESS_PDF, "source.pdf", b"%PDF-"),
    (ConversionOperation.TXT_TO_MARKDOWN, "source.txt", b"Hello"),
    (ConversionOperation.MARKDOWN_TO_PDF, "source.md", b"# Hello"),
    (ConversionOperation.IMAGES_TO_PDF, "source.png", b"\x89PNG\r\n\x1a\n"),
]


def test_every_operation_has_a_spec_and_converter():
    assert set(OPERATIONS) == set(ConversionOperation)
    assert set(CONVERTERS) == set(ConversionOperation)


def test_every_operation_has_a_library_group():
    assert all(spec.group for spec in OPERATIONS.values())


def test_operation_schema_exposes_group_and_suffix():
    out = OperationOut.from_spec(get_spec(ConversionOperation.COMPRESS_PDF))
    assert out.group == "PDF tools"
    assert out.outputSuffix == "-compressed"


@pytest.mark.parametrize(("operation", "filename", "prefix"), SIGNATURES)
def test_prefix_matches_the_canonical_signature(operation, filename, prefix):
    assert prefix_matches(operation, filename, prefix)


def test_output_filename_marks_compressed_files():
    assert output_filename("report.pdf", ConversionOperation.COMPRESS_PDF) == (
        "report-compressed.pdf"
    )
    assert output_filename("report.pdf", ConversionOperation.PDF_TO_TEXT) == "report.txt"
    assert output_filename("report.docx", ConversionOperation.DOCX_TO_MARKDOWN) == "report.md"


def test_validate_upload_metadata_accepts_presentation_types():
    name, extension, content_type = validate_upload_metadata(
        operation=ConversionOperation.PPTX_TO_PDF,
        filename="Quarterly deck.pptx",
        file_size=1024,
        content_type=("application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        max_bytes=25 * 1024 * 1024,
    )
    assert name == "Quarterly deck.pptx"
    assert extension == "pptx"
    assert content_type.endswith("presentationml.presentation")
