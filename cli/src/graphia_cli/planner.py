from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from graphia_cli.errors import UsageError
from graphia_cli.operations import (
    ALREADY_TARGET,
    Catalog,
    file_extension,
    normalize_operation_id,
    normalize_target,
)

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
}

STATE_READY = "ready"
STATE_SKIP = "skip"
STATE_ERROR = "error"


@dataclass
class PlanItem:
    source: Path
    relative: Path
    operation: str
    destination: Path
    size: int = 0
    state: str = STATE_READY
    reason: str | None = None
    operation_label: str = ""


@dataclass
class Plan:
    items: list[PlanItem] = field(default_factory=list)
    output_root: Path | None = None

    @property
    def ready(self) -> list[PlanItem]:
        return [item for item in self.items if item.state == STATE_READY]

    @property
    def skipped(self) -> list[PlanItem]:
        return [item for item in self.items if item.state == STATE_SKIP]

    @property
    def errors(self) -> list[PlanItem]:
        return [item for item in self.items if item.state == STATE_ERROR]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def _resolve(path: Path) -> Path:
    return path.expanduser().resolve()


def _walk_files(
    root: Path,
    *,
    recursive: bool,
    include_hidden: bool,
    output_root: Path | None,
) -> list[Path]:
    files: list[Path] = []
    output_key = (
        os.path.normcase(str(output_root.resolve())) if output_root is not None else None
    )

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        kept: list[str] = []
        for name in sorted(dirnames):
            if name in IGNORE_DIRS:
                continue
            if not include_hidden and name.startswith("."):
                continue
            candidate = (current / name).resolve()
            if output_key is not None and os.path.normcase(str(candidate)) == output_key:
                continue
            kept.append(name)
        dirnames[:] = kept if recursive else []

        for name in sorted(filenames):
            if not include_hidden and name.startswith("."):
                continue
            if name.startswith("~$"):
                continue
            candidate = current / name
            if not candidate.is_file():
                continue
            files.append(candidate)
        if not recursive:
            break
    return files


def _root_label(path: Path) -> str:
    return path.name or "documents"


def build_plan(
    paths: list[Path],
    *,
    target: str | None,
    operation: str | None,
    out: Path | None,
    recursive: bool,
    include_hidden: bool,
    overwrite: bool,
    max_upload_bytes: int,
    catalog: Catalog,
) -> Plan:
    if not paths:
        raise UsageError("Pass at least one file or folder.")
    if target and operation:
        raise UsageError("Use --to or --operation, not both.")
    if not target and not operation:
        raise UsageError("Choose a target with --to pdf|md|txt, or pass --operation.")

    target_format = normalize_target(target) if target else None
    explicit_operation = normalize_operation_id(operation) if operation else None
    if explicit_operation:
        catalog.get(explicit_operation)

    resolved_paths: list[Path] = []
    for value in paths:
        path = _resolve(value)
        if not path.exists():
            raise UsageError(f"Path not found: {value}")
        resolved_paths.append(path)

    single_file = len(resolved_paths) == 1 and resolved_paths[0].is_file()
    multiple_roots = len(resolved_paths) > 1

    if out is not None:
        output_root = _resolve(out)
    elif single_file:
        output_root = resolved_paths[0].parent
    else:
        output_root = (Path.cwd() / "graphia-output").resolve()

    sources: list[tuple[Path, Path, str | None]] = []
    for path in resolved_paths:
        if path.is_file():
            sources.append((path, Path(path.name), None))
            continue
        if not path.is_dir():
            raise UsageError(f"Unsupported path: {path}")
        label = _root_label(path)
        for file_path in _walk_files(
            path,
            recursive=recursive,
            include_hidden=include_hidden,
            output_root=output_root if not single_file else None,
        ):
            sources.append((file_path, file_path.relative_to(path), label))

    plan = Plan(output_root=output_root)
    destination_keys: dict[str, list[PlanItem]] = {}

    for source, relative, root_label in sources:
        name = source.name
        extension = file_extension(name)
        item: PlanItem

        chosen_operation = explicit_operation
        if chosen_operation is None:
            chosen_operation = catalog.infer(extension, target_format or "pdf")

        if not extension:
            item = PlanItem(
                source=source,
                relative=relative,
                operation=chosen_operation or "",
                destination=output_root / name,
                state=STATE_SKIP,
                reason="No file extension.",
            )
        elif chosen_operation is None:
            if extension in ALREADY_TARGET.get(target_format or "", set()):
                reason = f"Already {target_format.upper()}."
            else:
                reason = f"No {target_format} conversion for .{extension}."
            item = PlanItem(
                source=source,
                relative=relative,
                operation="",
                destination=output_root / name,
                state=STATE_SKIP,
                reason=reason,
            )
        elif not catalog.has(chosen_operation):
            item = PlanItem(
                source=source,
                relative=relative,
                operation=chosen_operation,
                destination=output_root / name,
                state=STATE_SKIP,
                reason="This server does not offer that conversion.",
            )
        elif not catalog.accepts(chosen_operation, extension):
            operation_spec = catalog.get(chosen_operation)
            accepted = ", ".join(f".{value}" for value in operation_spec.input_extensions)
            item = PlanItem(
                source=source,
                relative=relative,
                operation=chosen_operation,
                destination=output_root / name,
                state=STATE_SKIP,
                reason=f"{operation_spec.label} accepts {accepted}.",
            )
        else:
            output_name = catalog.output_name(chosen_operation, name)
            if single_file:
                destination = output_root / output_name
            elif multiple_roots and root_label is not None:
                destination = output_root / root_label / relative.parent / output_name
            elif multiple_roots:
                destination = output_root / output_name
            else:
                destination = output_root / relative.parent / output_name

            try:
                size = source.stat().st_size
            except OSError as exc:
                item = PlanItem(
                    source=source,
                    relative=relative,
                    operation=chosen_operation,
                    destination=destination,
                    state=STATE_ERROR,
                    reason=f"Could not read the file: {exc}",
                )
            else:
                if size <= 0:
                    item = PlanItem(
                        source=source,
                        relative=relative,
                        operation=chosen_operation,
                        destination=destination,
                        size=size,
                        state=STATE_SKIP,
                        reason="The file is empty.",
                    )
                elif size > max_upload_bytes:
                    item = PlanItem(
                        source=source,
                        relative=relative,
                        operation=chosen_operation,
                        destination=destination,
                        size=size,
                        state=STATE_SKIP,
                        reason=f"Larger than the {max_upload_bytes // (1024 * 1024)} MB limit.",
                    )
                else:
                    item = PlanItem(
                        source=source,
                        relative=relative,
                        operation=chosen_operation,
                        destination=destination,
                        size=size,
                    )

        if item.operation and catalog.has(item.operation):
            item.operation_label = catalog.get(item.operation).label
        plan.items.append(item)
        if item.state == STATE_READY:
            destination_keys.setdefault(str(item.destination).casefold(), []).append(item)

    for group in destination_keys.values():
        if len(group) < 2:
            continue
        for item in group:
            item.state = STATE_ERROR
            item.reason = (
                "Another source file would write the same output. "
                "Rename one or choose a different --out."
            )

    for item in plan.items:
        if item.state != STATE_READY:
            continue
        if item.destination.exists() and item.destination.is_dir():
            item.state = STATE_ERROR
            item.reason = "The output path is a directory."
        elif item.destination.exists() and not overwrite:
            item.state = STATE_SKIP
            item.reason = "Output already exists (pass --overwrite)."

    plan.items.sort(key=lambda item: str(item.source).casefold())
    return plan
