from __future__ import annotations

import re
from pathlib import Path

import mammoth
from markdownify import markdownify

from converters.base import ConversionContext, ConversionError, ConversionResult

_IMAGE_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    if input_path.suffix.lower() != ".docx":
        raise ConversionError("Expected a DOCX file.")

    try:
        with input_path.open("rb") as handle:
            document = mammoth.convert_to_html(handle)
    except Exception as exc:
        raise ConversionError("This file is not a valid DOCX document.") from exc

    # The output is a single Markdown file, so images are dropped rather than
    # inlined as base64 data URIs.
    html = _IMAGE_TAG.sub("", document.value)
    markdown = markdownify(
        html,
        heading_style="ATX",
        table_infer_header=True,
    ).strip()
    if not markdown:
        raise ConversionError("This document has no text to extract.")

    output = context.workdir / "result.md"
    output.write_text(f"{markdown}\n", encoding="utf-8")
    return ConversionResult(path=output, media_type="text/markdown", extension="md")
