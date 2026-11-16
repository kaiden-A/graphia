from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def to_ms(value: datetime | None) -> int | None:
    value = ensure_utc(value)
    return int(value.timestamp() * 1000) if value is not None else None


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def local_path(value: str | None, *, default: str = "/") -> str:
    """Allow only same-site paths for post-login redirects."""
    candidate = (value or "").strip()
    if not candidate.startswith("/") or candidate.startswith("//"):
        return default
    if "\\" in candidate or "\x00" in candidate:
        return default
    return candidate


_UNSAFE_FILENAME = re.compile(r"[^\w .()\-]+", re.UNICODE)
_MULTI_SPACE = re.compile(r"\s+")


def sanitize_filename(name: str, *, fallback: str = "document") -> str:
    """Keep a human-readable display filename only. Never use it as an object key."""
    raw = (name or "").replace("\\", "/").split("/")[-1]
    raw = unicodedata.normalize("NFKC", raw)
    raw = raw.replace("\x00", "").strip().strip(".")
    raw = _UNSAFE_FILENAME.sub("_", raw)
    raw = _MULTI_SPACE.sub(" ", raw).strip()
    if not raw:
        raw = fallback
    if len(raw) > 180:
        suffix = Path(raw).suffix[:16]
        stem = Path(raw).stem[: max(1, 180 - len(suffix))]
        raw = f"{stem}{suffix}"
    return raw


def filename_stem(name: str, *, fallback: str = "document") -> str:
    return Path(sanitize_filename(name, fallback=fallback)).stem or fallback


def content_disposition(filename: str) -> str:
    """RFC 5987-friendly attachment header for a presigned R2 GET."""
    safe = sanitize_filename(filename)
    ascii_name = safe.encode("ascii", "ignore").decode("ascii") or "download"
    ascii_name = ascii_name.replace('"', "") or "download"
    from urllib.parse import quote

    encoded = quote(safe, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"
