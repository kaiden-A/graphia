from __future__ import annotations

from pathlib import Path

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.pdf_text import extract_pages


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    if input_path.suffix.lower() != ".pdf":
        raise ConversionError("Expected a PDF file.")

    pages = extract_pages(input_path)
    body = "\n\n".join(text for text in pages if text)

    output = context.workdir / "result.txt"
    output.write_text(f"{body}\n", encoding="utf-8")
    return ConversionResult(path=output, media_type="text/plain", extension="txt")
