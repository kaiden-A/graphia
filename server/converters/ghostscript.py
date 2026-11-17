from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from converters.base import ConversionError

logger = logging.getLogger(__name__)


def resolve_ghostscript(ghostscript_bin: str) -> Path | None:
    """Return the Ghostscript binary as a file path, or None if it is missing."""
    if not ghostscript_bin.strip():
        return None

    candidate = Path(ghostscript_bin)
    if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
        return candidate

    found = shutil.which(ghostscript_bin)
    return Path(found) if found else None


def ghostscript_available(ghostscript_bin: str) -> bool:
    return resolve_ghostscript(ghostscript_bin) is not None


def compress(
    input_path: Path,
    output_path: Path,
    *,
    timeout_seconds: int,
    ghostscript_bin: str,
) -> Path:
    binary = resolve_ghostscript(ghostscript_bin)
    if binary is None:
        logger.error("Ghostscript was not found. GHOSTSCRIPT_BIN=%r", ghostscript_bin)
        raise ConversionError("Ghostscript is not installed on the conversion server.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(binary),
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.7",
        "-dPDFSETTINGS=/ebook",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        "-dSAFER",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.warning(
            "Ghostscript timed out after %ss compressing %s", timeout_seconds, input_path.name
        )
        raise ConversionError("The PDF compression timed out.") from exc
    except OSError as exc:
        logger.exception("Ghostscript could not start from %s", binary)
        raise ConversionError("Ghostscript could not start on the conversion server.") from exc

    if completed.returncode != 0 or not output_path.exists():
        detail = (
            completed.stderr or completed.stdout or "Ghostscript could not compress this PDF."
        ).strip()
        logger.warning(
            "Ghostscript failed for %s (exit %s): %s",
            input_path.name,
            completed.returncode,
            detail[:400],
        )
        raise ConversionError(detail[:400])

    with output_path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ConversionError("Ghostscript produced an invalid PDF.")

    return output_path
