from __future__ import annotations

import pytest

from graphia_cli.errors import UsageError
from graphia_cli.operations import Catalog, normalize_operation_id, normalize_target


def test_target_inference(catalog: Catalog):
    assert catalog.infer("pptx", "pdf") == "pptx_to_pdf"
    assert catalog.infer("docx", "pdf") == "docx_to_pdf"
    assert catalog.infer("xlsx", "pdf") == "xlsx_to_pdf"
    assert catalog.infer("png", "pdf") == "images_to_pdf"
    assert catalog.infer("jpeg", "pdf") == "images_to_pdf"
    assert catalog.infer("md", "pdf") == "markdown_to_pdf"
    assert catalog.infer("pdf", "md") == "pdf_to_markdown"
    assert catalog.infer("docx", "md") == "docx_to_markdown"
    assert catalog.infer("txt", "md") == "txt_to_markdown"
    assert catalog.infer("pdf", "txt") == "pdf_to_text"


def test_target_does_not_convert_already_done(catalog: Catalog):
    assert catalog.infer("pdf", "pdf") is None
    assert catalog.infer("md", "md") is None
    assert catalog.infer("txt", "txt") is None


def test_target_aliases():
    assert normalize_target("markdown") == "md"
    assert normalize_target(".PDF") == "pdf"
    assert normalize_target("text") == "txt"
    with pytest.raises(UsageError):
        normalize_target("docx")


def test_operation_id_normalization():
    assert normalize_operation_id("compress-pdf") == "compress_pdf"
    assert normalize_operation_id("PPTX_TO_PDF") == "pptx_to_pdf"


def test_output_names(catalog: Catalog):
    assert catalog.output_name("pptx_to_pdf", "deck.pptx") == "deck.pdf"
    assert catalog.output_name("compress_pdf", "deck.pdf") == "deck-compressed.pdf"
    assert catalog.output_name("pdf_to_markdown", "notes.v2.pdf") == "notes.v2.md"


def test_unknown_operation_is_rejected(catalog: Catalog):
    with pytest.raises(UsageError):
        catalog.get("not_a_real_operation")
