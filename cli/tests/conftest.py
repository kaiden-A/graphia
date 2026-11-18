from __future__ import annotations

from pathlib import Path

import pytest

from graphia_cli.api import Operation
from graphia_cli.config import Runtime
from graphia_cli.operations import Catalog


@pytest.fixture(autouse=True)
def no_keyring(monkeypatch):
    monkeypatch.setenv("GRAPHIA_NO_KEYRING", "1")
    monkeypatch.setattr("graphia_cli.client.time.sleep", lambda _seconds: None)
    monkeypatch.setattr("graphia_cli.runner.POLL_START_SECONDS", 0.01)


@pytest.fixture()
def runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        server="https://graphia.test",
        server_source="test",
        config_dir=tmp_path,
        config_path=tmp_path / "config.toml",
    )


def make_operations() -> list[Operation]:
    return [
        Operation(
            id="docx_to_pdf",
            label="DOCX to PDF",
            description="",
            group="Make a PDF",
            input_extensions=("docx",),
            output_extension="pdf",
        ),
        Operation(
            id="pptx_to_pdf",
            label="PPTX to PDF",
            description="",
            group="Make a PDF",
            input_extensions=("pptx",),
            output_extension="pdf",
        ),
        Operation(
            id="xlsx_to_pdf",
            label="XLSX to PDF",
            description="",
            group="Make a PDF",
            input_extensions=("xlsx",),
            output_extension="pdf",
        ),
        Operation(
            id="images_to_pdf",
            label="Image to PDF",
            description="",
            group="Make a PDF",
            input_extensions=("png", "jpg", "jpeg", "webp", "gif", "bmp", "tif", "tiff"),
            output_extension="pdf",
        ),
        Operation(
            id="markdown_to_pdf",
            label="Markdown to PDF",
            description="",
            group="Make a PDF",
            input_extensions=("md", "markdown"),
            output_extension="pdf",
        ),
        Operation(
            id="pdf_to_markdown",
            label="PDF to Markdown",
            description="",
            group="Read a PDF",
            input_extensions=("pdf",),
            output_extension="md",
        ),
        Operation(
            id="pdf_to_text",
            label="PDF to Text",
            description="",
            group="Read a PDF",
            input_extensions=("pdf",),
            output_extension="txt",
        ),
        Operation(
            id="compress_pdf",
            label="Compress PDF",
            description="",
            group="PDF tools",
            input_extensions=("pdf",),
            output_extension="pdf",
            output_suffix="-compressed",
        ),
        Operation(
            id="docx_to_markdown",
            label="DOCX to Markdown",
            description="",
            group="Make Markdown",
            input_extensions=("docx",),
            output_extension="md",
        ),
        Operation(
            id="txt_to_markdown",
            label="Text to Markdown",
            description="",
            group="Make Markdown",
            input_extensions=("txt",),
            output_extension="md",
        ),
    ]


@pytest.fixture()
def catalog() -> Catalog:
    return Catalog.from_operations(make_operations())
