from __future__ import annotations

from pathlib import Path

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.pdf_text import extract_pages


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    if input_path.suffix.lower() != ".pdf":
        raise ConversionError("Expected a PDF file.")

    pages = extract_pages(input_path)

    sections: list[str] = []
    for index, text in enumerate(pages, start=1):
        if text:
            sections.append(f"## Page {index}\n\n{text}")
        else:
            sections.append(f"## Page {index}\n\n_(No selectable text on this page.)_")

    title = Path(context.original_filename).stem
    body = "\n\n".join(sections)
    markdown = f"# {title}\n\n> Extracted from a {len(pages)}-page PDF.\n\n{body}\n"

    output = context.workdir / "result.md"
    output.write_text(markdown, encoding="utf-8")
    return ConversionResult(path=output, media_type="text/markdown", extension="md")
