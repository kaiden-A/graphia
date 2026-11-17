from __future__ import annotations

from pathlib import Path

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.ghostscript import compress


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    if input_path.suffix.lower() != ".pdf":
        raise ConversionError("Expected a PDF file.")

    compressed = context.workdir / "compressed.pdf"
    compress(
        input_path,
        compressed,
        timeout_seconds=context.timeout_seconds,
        ghostscript_bin=context.ghostscript_bin,
    )

    if compressed.stat().st_size >= input_path.stat().st_size:
        # Never hand back a file that is larger than the original.
        output = context.workdir / "result.pdf"
        output.write_bytes(input_path.read_bytes())
    else:
        output = compressed

    return ConversionResult(path=output, media_type="application/pdf", extension="pdf")
