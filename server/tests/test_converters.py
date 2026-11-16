from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from converters.base import ConversionContext
from converters.images_to_pdf import convert as images_to_pdf
from converters.libreoffice import soffice_available
from converters.markdown_to_pdf import render_markdown_html
from converters.pdf_to_markdown import convert as pdf_to_markdown
from converters.txt_to_markdown import convert as txt_to_markdown


@pytest.fixture()
def context(tmp_path: Path) -> ConversionContext:
    return ConversionContext(
        workdir=tmp_path,
        original_filename="source.txt",
        timeout_seconds=30,
        soffice_bin="soffice",
    )


def test_txt_to_markdown(context, tmp_path):
    source = tmp_path / "input.txt"
    source.write_text("First paragraph.\r\n\r\nSecond paragraph.\r\n", encoding="utf-8")
    result = txt_to_markdown(source, context)
    text = result.path.read_text(encoding="utf-8")
    assert text.startswith("# source")
    assert "First paragraph." in text
    assert "Second paragraph." in text
    assert result.extension == "md"


def test_pdf_to_markdown(context, tmp_path):
    source = tmp_path / "input.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Selectable text from a PDF.")
    document.save(source)
    document.close()

    result = pdf_to_markdown(source, context)
    text = result.path.read_text(encoding="utf-8")
    assert "Selectable text from a PDF." in text
    assert "## Page 1" in text


def test_pdf_to_markdown_rejects_empty_text(context, tmp_path):
    source = tmp_path / "input.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(source)
    document.close()

    with pytest.raises(Exception) as exc:
        pdf_to_markdown(source, context)
    assert "no selectable text" in str(exc.value).lower()


def test_images_to_pdf(context, tmp_path):
    source = tmp_path / "input.png"
    Image.new("RGB", (200, 100), "white").save(source)

    result = images_to_pdf(source, context)
    assert result.path.exists()
    assert result.path.read_bytes().startswith(b"%PDF-")


def test_markdown_render_escapes_raw_html_and_drops_images():
    rendered = render_markdown_html(
        "Hello <script>alert(1)</script>\n\n![alt text](https://example.com/x.png)",
        "Title",
    )
    assert "&lt;script&gt;" in rendered
    assert "<script>alert" not in rendered
    assert "<img" not in rendered
    assert "alt text" in rendered


@pytest.mark.skipif(not soffice_available("soffice"), reason="LibreOffice is not installed")
def test_docx_to_pdf_requires_soffice(context, tmp_path):
    from docx import Document

    from converters.docx_to_pdf import convert as docx_to_pdf

    source = tmp_path / "input.docx"
    document = Document()
    document.add_heading("Hello", level=1)
    document.add_paragraph("A DOCX conversion.")
    document.save(source)

    result = docx_to_pdf(source, context)
    assert result.path.read_bytes().startswith(b"%PDF-")
