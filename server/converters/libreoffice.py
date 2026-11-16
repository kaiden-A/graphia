from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

from converters.base import ConversionError


def soffice_available(soffice_bin: str) -> bool:
    return bool(shutil.which(soffice_bin) or Path(soffice_bin).exists())


def convert_to_pdf(
    input_path: Path,
    workdir: Path,
    *,
    timeout_seconds: int,
    soffice_bin: str,
) -> Path:
    output_dir = workdir / "soffice-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = workdir / f"lo-profile-{uuid.uuid4().hex[:8]}"
    profile_dir.mkdir(parents=True, exist_ok=True)

    command = [
        soffice_bin,
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
    except FileNotFoundError as exc:
        raise ConversionError(
            "LibreOffice is not installed on the conversion server."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ConversionError("The document conversion timed out.") from exc

    expected = output_dir / f"{input_path.stem}.pdf"
    if completed.returncode != 0 or not expected.exists():
        detail = (
            completed.stderr
            or completed.stdout
            or "LibreOffice could not convert this file."
        ).strip()
        raise ConversionError(detail[:400])

    with expected.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ConversionError("LibreOffice produced an invalid PDF.")

    return expected
