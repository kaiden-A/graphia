from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConversionError(Exception):
    """A conversion failure with a message that is safe to show to the user."""


@dataclass(frozen=True)
class ConversionContext:
    workdir: Path
    original_filename: str
    timeout_seconds: int
    soffice_bin: str


@dataclass(frozen=True)
class ConversionResult:
    path: Path
    media_type: str
    extension: str
