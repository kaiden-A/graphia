from __future__ import annotations

from pathlib import Path

import pymupdf
from pypdf import PdfReader

from converters.base import ConversionContext, ConversionError, ConversionResult

MAX_PAGES = 500


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    if input_path.suffix.lower() != ".pdf":
        raise ConversionError("Expected a PDF file.")

    try:
        reader = PdfReader(str(input_path))
    except Exception as exc:
        raise ConversionError("This PDF could not be opened.") from exc

    if reader.is_encrypted:
        raise ConversionError("This PDF is password-protected. Remove the password and try again.")
    if len(reader.pages) > MAX_PAGES:
        raise ConversionError(f"This PDF has more than {MAX_PAGES} pages.")

    try:
        document = pymupdf.open(input_path)
    except Exception as exc:
        raise ConversionError("This PDF could not be read.") from exc

    sections: list[str] = []
    total_text = 0
    for index, page in enumerate(document, start=1):
        text = page.get_text("text").strip()
        total_text += len(text)
        if text:
            sections.append(f"## Page {index}\n\n{text}")
        else:
            sections.append(f"## Page {index}\n\n_(No selectable text on this page.)_")

    if total_text < 20:
        raise ConversionError(
            "This PDF has no selectable text. Scanned PDFs need OCR, which is not supported yet."
        )

    title = Path(context.original_filename).stem
    body = "\n\n".join(sections)
    markdown = f"# {title}\n\n> Extracted from a {len(reader.pages)}-page PDF.\n\n{body}\n"

    output = context.workdir / "result.md"
    output.write_text(markdown, encoding="utf-8")
    return ConversionResult(path=output, media_type="text/markdown", extension="md")
