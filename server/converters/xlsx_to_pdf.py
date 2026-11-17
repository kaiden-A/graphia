from __future__ import annotations

from pathlib import Path

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.libreoffice import convert_to_pdf


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    if input_path.suffix.lower() != ".xlsx":
        raise ConversionError("Expected an XLSX file.")

    output = convert_to_pdf(
        input_path,
        context.workdir,
        timeout_seconds=context.timeout_seconds,
        soffice_bin=context.soffice_bin,
    )
    return ConversionResult(
        path=output,
        media_type="application/pdf",
        extension="pdf",
    )
