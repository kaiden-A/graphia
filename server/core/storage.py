from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.config import settings
from core.utils import content_disposition

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObjectInfo:
    size: int
    content_type: str | None
    etag: str | None


class Storage(Protocol):
    def put_file(self, key: str, path: Path, content_type: str) -> None: ...
    def put_bytes(self, key: str, data: bytes, content_type: str) -> None: ...
    def download_to(self, key: str, path: Path) -> None: ...
    def head(self, key: str) -> ObjectInfo | None: ...
    def read_range(self, key: str, start: int, end: int) -> bytes: ...
    def presign_put(self, key: str, content_type: str, expires_in: int) -> str: ...
    def presign_get(self, key: str, filename: str, expires_in: int) -> str: ...
    def delete(self, key: str) -> None: ...


class R2Storage:
    def __init__(self) -> None:
        self.bucket = settings.r2_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url or None,
            aws_access_key_id=settings.r2_access_key_id or None,
            aws_secret_access_key=settings.r2_secret_access_key or None,
            region_name=settings.r2_region,
            config=Config(
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def put_file(self, key: str, path: Path, content_type: str) -> None:
        self.client.upload_file(
            str(path),
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def download_to(self, key: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, str(path))

    def head(self, key: str) -> ObjectInfo | None:
        try:
            data = self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        return ObjectInfo(
            size=int(data.get("ContentLength", 0)),
            content_type=data.get("ContentType"),
            etag=data.get("ETag"),
        )

    def read_range(self, key: str, start: int, end: int) -> bytes:
        data = self.client.get_object(
            Bucket=self.bucket,
            Key=key,
            Range=f"bytes={start}-{end}",
        )
        return data["Body"].read()

    def presign_put(self, key: str, content_type: str, expires_in: int) -> str:
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    def presign_get(self, key: str, filename: str, expires_in: int) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ResponseContentDisposition": content_disposition(filename),
            },
            ExpiresIn=expires_in,
        )

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError:
            logger.warning("Could not delete R2 object", extra={"key": key}, exc_info=True)


@lru_cache
def get_storage() -> Storage:
    return R2Storage()
