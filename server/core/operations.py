from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.errors import AppError
from core.models.enums import ConversionOperation
from core.utils import filename_stem, sanitize_filename

IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "webp", "gif", "bmp", "tif", "tiff")
IMAGE_TYPES = (
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/tiff",
)


@dataclass(frozen=True)
class OperationSpec:
    id: ConversionOperation
    label: str
    description: str
    input_extensions: tuple[str, ...]
    output_extension: str
    output_media_type: str


OPERATIONS: dict[ConversionOperation, OperationSpec] = {
    ConversionOperation.DOCX_TO_PDF: OperationSpec(
        id=ConversionOperation.DOCX_TO_PDF,
        label="DOCX to PDF",
        description="Convert a Word document into a print-ready PDF.",
        input_extensions=("docx",),
        output_extension="pdf",
        output_media_type="application/pdf",
    ),
    ConversionOperation.PDF_TO_MARKDOWN: OperationSpec(
        id=ConversionOperation.PDF_TO_MARKDOWN,
        label="PDF to Markdown",
        description="Extract selectable text from a PDF, page by page.",
        input_extensions=("pdf",),
        output_extension="md",
        output_media_type="text/markdown",
    ),
    ConversionOperation.TXT_TO_MARKDOWN: OperationSpec(
        id=ConversionOperation.TXT_TO_MARKDOWN,
        label="Text to Markdown",
        description="Turn a plain text file into clean Markdown paragraphs.",
        input_extensions=("txt",),
        output_extension="md",
        output_media_type="text/markdown",
    ),
    ConversionOperation.MARKDOWN_TO_PDF: OperationSpec(
        id=ConversionOperation.MARKDOWN_TO_PDF,
        label="Markdown to PDF",
        description="Render Markdown as a styled PDF document.",
        input_extensions=("md", "markdown"),
        output_extension="pdf",
        output_media_type="application/pdf",
    ),
    ConversionOperation.IMAGES_TO_PDF: OperationSpec(
        id=ConversionOperation.IMAGES_TO_PDF,
        label="Image to PDF",
        description="Place one image on a single PDF page.",
        input_extensions=IMAGE_EXTENSIONS,
        output_extension="pdf",
        output_media_type="application/pdf",
    ),
}


def get_spec(operation: ConversionOperation) -> OperationSpec:
    return OPERATIONS[operation]


def file_extension(filename: str) -> str:
    return Path(sanitize_filename(filename)).suffix.lower().lstrip(".")


def canonical_content_type(operation: ConversionOperation, filename: str) -> str:
    ext = file_extension(filename)
    mapping = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
        "txt": "text/plain",
        "md": "text/markdown",
        "markdown": "text/markdown",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tif": "image/tiff",
        "tiff": "image/tiff",
    }
    if ext not in get_spec(operation).input_extensions:
        raise AppError(415, "The file extension does not match the selected conversion.")
    return mapping[ext]


def validate_upload_metadata(
    *,
    operation: ConversionOperation,
    filename: str,
    file_size: int,
    content_type: str,
    max_bytes: int,
) -> tuple[str, str, str]:
    """Return (safe_filename, extension, canonical_content_type)."""
    safe_name = sanitize_filename(filename)
    ext = file_extension(safe_name)
    spec = get_spec(operation)

    if ext not in spec.input_extensions:
        accepted = ", ".join(f".{item}" for item in spec.input_extensions)
        raise AppError(415, f"{spec.label} accepts {accepted} files.")

    if file_size <= 0:
        raise AppError(422, "The file is empty.")
    if file_size > max_bytes:
        raise AppError(
            413,
            f"The file is larger than {max_bytes // (1024 * 1024)} MB.",
        )

    declared = (content_type or "").split(";")[0].strip().lower()
    allowed: set[str] = set()
    for item in spec.input_extensions:
        allowed.add(canonical_content_type(operation, f"source.{item}").lower())
    if operation in {
        ConversionOperation.TXT_TO_MARKDOWN,
        ConversionOperation.MARKDOWN_TO_PDF,
    }:
        allowed.update({"text/plain", "text/markdown", "text/x-markdown"})
    image_alias = operation is ConversionOperation.IMAGES_TO_PDF and declared.startswith("image/")
    if (
        declared
        and declared not in allowed
        and declared != "application/octet-stream"
        and not image_alias
    ):
        raise AppError(415, "The file content type does not match the selected conversion.")

    canonical = canonical_content_type(operation, safe_name)
    return safe_name, ext, canonical


def prefix_matches(operation: ConversionOperation, filename: str, prefix: bytes) -> bool:
    """Cheap first-bytes check performed by Service A after the direct upload."""
    ext = file_extension(filename)
    if operation is ConversionOperation.DOCX_TO_PDF:
        return prefix.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
    if operation is ConversionOperation.PDF_TO_MARKDOWN:
        return prefix.startswith(b"%PDF-")
    if operation is ConversionOperation.TXT_TO_MARKDOWN:
        return b"\x00" not in prefix
    if operation is ConversionOperation.MARKDOWN_TO_PDF:
        return b"\x00" not in prefix
    if operation is ConversionOperation.IMAGES_TO_PDF:
        signatures = {
            "png": (b"\x89PNG\r\n\x1a\n",),
            "jpg": (b"\xff\xd8\xff",),
            "jpeg": (b"\xff\xd8\xff",),
            "webp": (b"RIFF",),
            "gif": (b"GIF87a", b"GIF89a"),
            "bmp": (b"BM",),
            "tif": (b"II*\x00", b"MM\x00*"),
            "tiff": (b"II*\x00", b"MM\x00*"),
        }
        if ext == "webp":
            return len(prefix) >= 12 and prefix[:4] == b"RIFF" and prefix[8:12] == b"WEBP"
        return prefix.startswith(signatures.get(ext, ()))
    return False


def output_filename(original_filename: str, operation: ConversionOperation) -> str:
    spec = get_spec(operation)
    return f"{filename_stem(original_filename)}.{spec.output_extension}"
