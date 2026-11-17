from __future__ import annotations

import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from converters.base import ConversionError

logger = logging.getLogger(__name__)


def resolve_soffice(soffice_bin: str) -> Path | None:
    """Return the LibreOffice binary as a file path, or None if it is missing."""
    if not soffice_bin.strip():
        return None

    candidate = Path(soffice_bin)
    if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
        return candidate

    found = shutil.which(soffice_bin)
    return Path(found) if found else None


def soffice_available(soffice_bin: str) -> bool:
    return resolve_soffice(soffice_bin) is not None


def convert_to_pdf(
    input_path: Path,
    workdir: Path,
    *,
    timeout_seconds: int,
    soffice_bin: str,
) -> Path:
    binary = resolve_soffice(soffice_bin)
    if binary is None:
        logger.error("LibreOffice was not found. SOFFICE_BIN=%r", soffice_bin)
        raise ConversionError("LibreOffice is not installed on the conversion server.")

    output_dir = workdir / "soffice-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = workdir / f"lo-profile-{uuid.uuid4().hex[:8]}"
    profile_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(binary),
        "--headless",
        "--norestore",
        "--invisible",
        "--nodefault",
        "--nolockcheck",
        f"-env:UserInstallation={profile_dir.as_uri()}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(input_path),
    ]

    env = os.environ.copy()
    env["HOME"] = str(workdir)
    if os.name == "nt":
        env["USERPROFILE"] = str(workdir)

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        logger.warning(
            "LibreOffice timed out after %ss converting %s",
            timeout_seconds,
            input_path.name,
        )
        raise ConversionError("The document conversion timed out.") from exc
    except OSError as exc:
        logger.exception("LibreOffice could not start from %s", binary)
        raise ConversionError("LibreOffice could not start on the conversion server.") from exc

    expected = output_dir / f"{input_path.stem}.pdf"
    if completed.returncode != 0 or not expected.exists():
        detail = (
            completed.stderr
            or completed.stdout
            or "LibreOffice could not convert this file."
        ).strip()
        logger.warning(
            "LibreOffice failed for %s (exit %s): %s",
            input_path.name,
            completed.returncode,
            detail[:400],
        )
        raise ConversionError(detail[:400])

    with expected.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ConversionError("LibreOffice produced an invalid PDF.")

    return expected
