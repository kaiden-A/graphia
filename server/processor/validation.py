from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

from converters.base import ConversionError
from core.models.enums import ConversionOperation

MAX_DOCX_UNCOMPRESSED = 200 * 1024 * 1024
MAX_DOCX_SINGLE_FILE = 100 * 1024 * 1024
MAX_PDF_PAGES = 500
MAX_IMAGE_PIXELS = 50_000_000
MAX_IMAGE_DIMENSION = 10_000
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF"}


def _validate_docx(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ConversionError("This file is not a valid DOCX document.")
            total = 0
            for info in archive.infolist():
                name = info.filename
                normalized = name.replace("\\", "/")
                if (
                    normalized.startswith("/")
                    or ".." in normalized.split("/")
                    or ":" in normalized
                ):
                    raise ConversionError("This DOCX contains an unsafe path.")
                if info.file_size > MAX_DOCX_SINGLE_FILE:
                    raise ConversionError("This DOCX contains a file that is too large.")
                if info.compress_size and info.file_size / info.compress_size > 100:
                    raise ConversionError("This DOCX compression ratio is not safe.")
                total += info.file_size
                if total > MAX_DOCX_UNCOMPRESSED:
                    raise ConversionError("This DOCX expands to more than the allowed size.")
    except zipfile.BadZipFile as exc:
        raise ConversionError("This file is not a valid DOCX document.") from exc


def _validate_pdf(path: Path) -> None:
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ConversionError("This file is not a valid PDF.")
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ConversionError("This PDF could not be opened.") from exc
    if reader.is_encrypted:
        raise ConversionError("This PDF is password-protected. Remove the password and try again.")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ConversionError(f"This PDF has more than {MAX_PDF_PAGES} pages.")


def _validate_image(path: Path) -> None:
    try:
        with Image.open(path) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ConversionError("This image format is not supported.")
            width, height = image.size
            if (
                width > MAX_IMAGE_DIMENSION
                or height > MAX_IMAGE_DIMENSION
                or width * height > MAX_IMAGE_PIXELS
            ):
                raise ConversionError("This image is too large to convert safely.")
            image.verify()
    except ConversionError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise ConversionError("This image could not be read.") from exc


def _validate_text(path: Path) -> None:
    data = path.read_bytes()
    if b"\x00" in data:
        raise ConversionError("This text file contains binary data.")
    try:
        data.decode("utf-8-sig")
        return
    except UnicodeDecodeError:
        pass
    try:
        data.decode("cp1252")
    except UnicodeDecodeError as exc:
        raise ConversionError("This text file is not valid UTF-8 or Windows-1252.") from exc


def validate_input(operation: ConversionOperation, path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise ConversionError("The uploaded file is empty.")

    if operation is ConversionOperation.DOCX_TO_PDF:
        _validate_docx(path)
    elif operation is ConversionOperation.PDF_TO_MARKDOWN:
        _validate_pdf(path)
    elif operation is ConversionOperation.IMAGES_TO_PDF:
        _validate_image(path)
    elif operation in {ConversionOperation.TXT_TO_MARKDOWN, ConversionOperation.MARKDOWN_TO_PDF}:
        _validate_text(path)
