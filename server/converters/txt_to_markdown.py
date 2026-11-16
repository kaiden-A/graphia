from __future__ import annotations

import re
from pathlib import Path

from charset_normalizer import from_bytes

from converters.base import ConversionContext, ConversionError, ConversionResult

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_BLANK_LINES = re.compile(r"\n{3,}")


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    match = from_bytes(data).best()
    if match is not None:
        return str(match)
    return data.decode("cp1252", errors="replace")


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    try:
        text = _decode(input_path.read_bytes())
    except Exception as exc:
        raise ConversionError("This text file could not be read.") from exc

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL.sub("", text).strip()
    if not text:
        raise ConversionError("This text file is empty.")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        raise ConversionError("This text file is empty.")

    body = _BLANK_LINES.sub("\n\n", "\n\n".join(paragraphs))
    title = Path(context.original_filename).stem
    markdown = f"# {title}\n\n{body}\n"

    output = context.workdir / "result.md"
    output.write_text(markdown, encoding="utf-8")
    return ConversionResult(path=output, media_type="text/markdown", extension="md")
