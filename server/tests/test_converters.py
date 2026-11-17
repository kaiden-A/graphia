from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from converters.base import ConversionContext, ConversionError
from converters.compress_pdf import convert as compress_pdf
from converters.docx_to_markdown import convert as docx_to_markdown
from converters.ghostscript import ghostscript_available, resolve_ghostscript
from converters.images_to_pdf import convert as images_to_pdf
from converters.libreoffice import resolve_soffice, soffice_available
from converters.markdown_to_pdf import render_markdown_html
from converters.pdf_to_markdown import convert as pdf_to_markdown
from converters.pdf_to_text import convert as pdf_to_text
from converters.pptx_to_pdf import convert as pptx_to_pdf
from converters.txt_to_markdown import convert as txt_to_markdown
from converters.xlsx_to_pdf import convert as xlsx_to_pdf
from core.config import settings


@pytest.fixture()
def context(tmp_path: Path) -> ConversionContext:
    return ConversionContext(
        workdir=tmp_path,
        original_filename="source.txt",
        timeout_seconds=30,
        soffice_bin=settings.soffice_bin,
        ghostscript_bin=settings.ghostscript_bin,
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


def test_pdf_to_text(context, tmp_path):
    source = tmp_path / "input.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Selectable text from a PDF.")
    document.save(source)
    document.close()

    result = pdf_to_text(source, context)
    text = result.path.read_text(encoding="utf-8")
    assert "Selectable text from a PDF." in text
    assert "## Page" not in text
    assert result.extension == "txt"
    assert result.media_type == "text/plain"


def test_pdf_to_text_rejects_empty_text(context, tmp_path):
    source = tmp_path / "input.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(source)
    document.close()

    with pytest.raises(Exception) as exc:
        pdf_to_text(source, context)
    assert "no selectable text" in str(exc.value).lower()


def test_docx_to_markdown(context, tmp_path):
    from docx import Document

    source = tmp_path / "input.docx"
    document = Document()
    document.add_heading("Hello", level=1)
    document.add_paragraph("A DOCX conversion.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Name"
    table.rows[0].cells[1].text = "Value"
    document.save(source)

    result = docx_to_markdown(source, context)
    text = result.path.read_text(encoding="utf-8")
    assert "# Hello" in text
    assert "A DOCX conversion." in text
    assert "Name" in text
    assert "Value" in text
    assert "| Name | Value |" in text
    assert result.extension == "md"


def test_docx_to_markdown_drops_images(context, tmp_path):
    from docx import Document

    source = tmp_path / "input.docx"
    image = tmp_path / "pixel.png"
    Image.new("RGB", (10, 10), "red").save(image)
    document = Document()
    document.add_paragraph("Before the image.")
    document.add_picture(str(image))
    document.add_paragraph("After the image.")
    document.save(source)

    text = docx_to_markdown(source, context).path.read_text(encoding="utf-8")
    assert "Before the image." in text
    assert "After the image." in text
    assert "![" not in text
    assert "data:image" not in text


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


def test_markdown_render_keeps_a_leading_h1():
    rendered = render_markdown_html("# Own title\n\nBody text.", "report")
    assert "<h1>Own title</h1>" in rendered
    assert "<h1>report</h1>" not in rendered
    assert rendered.count("<h1>") == 1


def test_markdown_render_uses_the_filename_without_an_h1():
    rendered = render_markdown_html("Body text only.", "notes")
    assert "<h1>notes</h1>" in rendered


def test_resolve_soffice_returns_an_existing_file(tmp_path):
    fake = tmp_path / "soffice.exe"
    fake.write_text("stub", encoding="utf-8")
    fake.chmod(0o755)
    assert resolve_soffice(str(fake)) == fake


def test_resolve_soffice_rejects_a_directory(tmp_path):
    assert resolve_soffice(str(tmp_path)) is None


@pytest.mark.skipif(
    not soffice_available(settings.soffice_bin), reason="LibreOffice is not installed"
)
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


def test_resolve_ghostscript_returns_an_existing_file(tmp_path):
    fake = tmp_path / "gswin64c.exe"
    fake.write_text("stub", encoding="utf-8")
    fake.chmod(0o755)
    assert resolve_ghostscript(str(fake)) == fake


def test_resolve_ghostscript_rejects_a_directory(tmp_path):
    assert resolve_ghostscript(str(tmp_path)) is None


@pytest.mark.skipif(
    not soffice_available(settings.soffice_bin), reason="LibreOffice is not installed"
)
def test_pptx_to_pdf_requires_soffice(context, tmp_path):
    from pptx import Presentation

    source = tmp_path / "input.pptx"
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.shapes.title.text = "Graphia deck"
    presentation.save(source)

    result = pptx_to_pdf(source, context)
    assert result.path.read_bytes().startswith(b"%PDF-")


@pytest.mark.skipif(
    not soffice_available(settings.soffice_bin), reason="LibreOffice is not installed"
)
def test_xlsx_to_pdf_requires_soffice(context, tmp_path):
    from openpyxl import Workbook

    source = tmp_path / "input.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "Graphia"
    sheet["A2"] = 42
    workbook.save(source)

    result = xlsx_to_pdf(source, context)
    assert result.path.read_bytes().startswith(b"%PDF-")


def test_compress_pdf_reports_missing_ghostscript(context, tmp_path):
    source = tmp_path / "input.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(source)
    document.close()

    with pytest.raises(ConversionError) as exc:
        compress_pdf(source, replace(context, ghostscript_bin=""))
    assert "Ghostscript is not installed" in str(exc.value)


@pytest.mark.skipif(
    not ghostscript_available(settings.ghostscript_bin),
    reason="Ghostscript is not installed",
)
def test_compress_pdf_requires_ghostscript(context, tmp_path):
    source = tmp_path / "input.pdf"
    image = Image.effect_noise((800, 800), 100).convert("RGB")
    image.save(source, "PDF", resolution=300)

    result = compress_pdf(source, context)
    assert result.path.read_bytes().startswith(b"%PDF-")
    assert result.path.stat().st_size > 0
