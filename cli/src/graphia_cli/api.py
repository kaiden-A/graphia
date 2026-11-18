from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from graphia_cli.client import GraphiaClient
from graphia_cli.errors import NetworkError


def _expect_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NetworkError("The server returned an unexpected response.")
    return value


def _expect_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise NetworkError("The server returned an unexpected response.")
    return value


@dataclass(frozen=True)
class ConfigInfo:
    app_name: str
    version: str
    web_url: str
    auth_mode: str
    max_upload_mb: int
    max_active_jobs: int
    uploads_per_hour: int
    job_expiry_hours: int


@dataclass(frozen=True)
class UserInfo:
    id: str
    email: str
    name: str | None
    is_guest: bool


@dataclass(frozen=True)
class Operation:
    id: str
    label: str
    description: str
    group: str
    input_extensions: tuple[str, ...]
    output_extension: str
    output_suffix: str = ""


@dataclass(frozen=True)
class UploadTicket:
    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Conversion:
    id: str
    operation: str
    operation_label: str
    original_filename: str
    status: str
    error_message: str | None
    output_filename: str | None
    download_available: bool
    expires_at: int | None


def get_config(client: GraphiaClient) -> ConfigInfo:
    data = _expect_dict(client.json("GET", "/api/config"))
    limits = _expect_dict(data.get("limits"))
    auth = _expect_dict(data.get("auth"))
    return ConfigInfo(
        app_name=str(data.get("appName") or "Graphia"),
        version=str(data.get("version") or ""),
        web_url=str(data.get("webUrl") or client.server),
        auth_mode=str(auth.get("mode") or ""),
        max_upload_mb=int(limits.get("maxUploadMb") or 25),
        max_active_jobs=max(1, int(limits.get("maxActiveJobs") or 3)),
        uploads_per_hour=int(limits.get("uploadsPerHour") or 0),
        job_expiry_hours=int(limits.get("jobExpiryHours") or 24),
    )


def get_operations(client: GraphiaClient) -> list[Operation]:
    rows = _expect_list(client.json("GET", "/api/operations"))
    operations: list[Operation] = []
    for row in rows:
        item = _expect_dict(row)
        operations.append(
            Operation(
                id=str(item["id"]),
                label=str(item.get("label") or item["id"]),
                description=str(item.get("description") or ""),
                group=str(item.get("group") or ""),
                input_extensions=tuple(
                    str(value).lower().lstrip(".")
                    for value in item.get("inputExtensions") or []
                ),
                output_extension=str(item.get("outputExtension") or "").lstrip("."),
                output_suffix=str(item.get("outputSuffix") or ""),
            )
        )
    return operations


def get_me(client: GraphiaClient) -> UserInfo:
    data = _expect_dict(client.json("GET", "/api/auth/me"))
    return UserInfo(
        id=str(data.get("id") or ""),
        email=str(data.get("email") or ""),
        name=data.get("name") if isinstance(data.get("name"), str) else None,
        is_guest=bool(data.get("isGuest")),
    )


def create_conversion(
    client: GraphiaClient,
    *,
    operation: str,
    filename: str,
    file_size: int,
    content_type: str = "application/octet-stream",
) -> tuple[Conversion, UploadTicket]:
    data = _expect_dict(
        client.json(
            "POST",
            "/api/conversions",
            json={
                "operation": operation,
                "originalFilename": filename,
                "fileSize": file_size,
                "contentType": content_type,
            },
        )
    )
    job = _parse_conversion(_expect_dict(data.get("job")))
    upload = _expect_dict(data.get("upload"))
    ticket = UploadTicket(
        url=str(upload.get("url") or ""),
        method=str(upload.get("method") or "PUT"),
        headers={
            str(key): str(value)
            for key, value in _expect_dict(upload.get("headers")).items()
        },
    )
    return job, ticket


def _parse_conversion(data: dict[str, Any]) -> Conversion:
    return Conversion(
        id=str(data["id"]),
        operation=str(data.get("operation") or ""),
        operation_label=str(data.get("operationLabel") or ""),
        original_filename=str(data.get("originalFilename") or ""),
        status=str(data.get("status") or ""),
        error_message=(
            data.get("errorMessage") if isinstance(data.get("errorMessage"), str) else None
        ),
        output_filename=(
            data.get("outputFilename")
            if isinstance(data.get("outputFilename"), str)
            else None
        ),
        download_available=bool(data.get("downloadAvailable")),
        expires_at=(
            int(data["expiresAt"]) if isinstance(data.get("expiresAt"), int) else None
        ),
    )


def complete_upload(client: GraphiaClient, job_id: str) -> Conversion:
    data = _expect_dict(
        client.json("POST", f"/api/conversions/{job_id}/complete-upload")
    )
    return _parse_conversion(data)


def get_conversion(client: GraphiaClient, job_id: str) -> Conversion:
    data = _expect_dict(client.json("GET", f"/api/conversions/{job_id}"))
    return _parse_conversion(data)


def get_download(client: GraphiaClient, job_id: str) -> str:
    data = _expect_dict(client.json("GET", f"/api/conversions/{job_id}/download"))
    url = data.get("url")
    if not isinstance(url, str) or not url:
        raise NetworkError("The server did not return a download link.")
    return url


def delete_conversion(client: GraphiaClient, job_id: str) -> None:
    client.json("DELETE", f"/api/conversions/{job_id}")


def logout(client: GraphiaClient) -> None:
    client.json("POST", "/api/cli/logout")
