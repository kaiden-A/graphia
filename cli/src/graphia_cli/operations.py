from __future__ import annotations

from dataclasses import dataclass

from graphia_cli.api import Operation
from graphia_cli.errors import UsageError

IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "webp", "gif", "bmp", "tif", "tiff")

TARGET_ALIASES = {
    "pdf": "pdf",
    "md": "md",
    "markdown": "md",
    "txt": "txt",
    "text": "txt",
}

TO_PDF = {
    "docx": "docx_to_pdf",
    "pptx": "pptx_to_pdf",
    "xlsx": "xlsx_to_pdf",
    "md": "markdown_to_pdf",
    "markdown": "markdown_to_pdf",
    **{extension: "images_to_pdf" for extension in IMAGE_EXTENSIONS},
}
TO_MD = {
    "pdf": "pdf_to_markdown",
    "docx": "docx_to_markdown",
    "txt": "txt_to_markdown",
}
TO_TXT = {"pdf": "pdf_to_text"}
TARGET_MAP = {"pdf": TO_PDF, "md": TO_MD, "txt": TO_TXT}

ALREADY_TARGET = {
    "pdf": {"pdf"},
    "md": {"md", "markdown"},
    "txt": {"txt"},
}


def normalize_target(value: str) -> str:
    target = TARGET_ALIASES.get((value or "").strip().lower().lstrip("."))
    if target is None:
        choices = ", ".join(sorted(TARGET_MAP))
        raise UsageError(f"Unsupported target format: {value}. Use one of: {choices}.")
    return target


def normalize_operation_id(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_")


def file_extension(path_name: str) -> str:
    name = path_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


@dataclass(frozen=True)
class Catalog:
    operations: tuple[Operation, ...]

    @classmethod
    def from_operations(cls, operations: list[Operation]) -> Catalog:
        return cls(operations=tuple(operations))

    def by_id(self) -> dict[str, Operation]:
        return {operation.id: operation for operation in self.operations}

    def get(self, operation_id: str) -> Operation:
        normalized = normalize_operation_id(operation_id)
        for operation in self.operations:
            if operation.id == normalized:
                return operation
        raise UsageError(
            f"Unknown operation: {operation_id}. Run `graphia operations` to list them."
        )

    def has(self, operation_id: str) -> bool:
        normalized = normalize_operation_id(operation_id)
        return any(operation.id == normalized for operation in self.operations)

    def infer(self, extension: str, target: str) -> str | None:
        return TARGET_MAP[target].get(extension.lower().lstrip("."))

    def accepts(self, operation_id: str, extension: str) -> bool:
        operation = self.get(operation_id)
        return extension.lower().lstrip(".") in operation.input_extensions

    def output_name(self, operation_id: str, source_name: str) -> str:
        operation = self.get(operation_id)
        stem = source_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if "." in stem:
            stem = stem.rsplit(".", 1)[0]
        if not stem:
            stem = "document"
        return f"{stem}{operation.output_suffix}.{operation.output_extension}"
