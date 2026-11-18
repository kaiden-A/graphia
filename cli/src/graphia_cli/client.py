from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from graphia_cli import __version__
from graphia_cli.errors import ApiError, NetworkError

JSON_HEADERS = {"Accept": "application/json"}
DEFAULT_MESSAGES = {
    401: "Your session is not valid.",
    403: "You do not have access to that.",
    404: "That resource was not found.",
    409: "That request conflicts with the current state.",
    410: "That request has expired.",
    413: "The file is too large.",
    415: "The file type does not match the conversion.",
    429: "Too many requests.",
    500: "The server had a problem.",
    502: "The server is unavailable.",
    503: "The server is unavailable.",
    504: "The server is unavailable.",
}


class GraphiaClient:
    def __init__(
        self,
        server: str,
        token: str | None = None,
        *,
        verbose: bool = False,
        timeout: float = 30.0,
    ) -> None:
        headers = {
            **JSON_HEADERS,
            "User-Agent": f"graphia-cli/{__version__}",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.server = server.rstrip("/")
        self.verbose = verbose
        self._http = httpx.Client(
            base_url=self.server,
            headers=headers,
            timeout=httpx.Timeout(timeout, connect=10.0),
            follow_redirects=False,
        )

    def __enter__(self) -> GraphiaClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _debug(self, method: str, path: str) -> None:
        if self.verbose:
            print(f"  {method} {path}", file=sys.stderr)

    def request(
        self,
        method: str,
        path: str,
        *,
        retries: int = 2,
        **kwargs: Any,
    ) -> httpx.Response:
        self._debug(method, path)
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                response = self._http.request(method, path, **kwargs)
            except httpx.TimeoutException as exc:
                last_error = exc
            except httpx.RequestError as exc:
                last_error = exc
            else:
                if response.status_code in {502, 503, 504} and attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                return response

            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))

        raise NetworkError(
            f"Could not reach {self.server}. Check your connection and the server URL."
        ) from last_error

    def json(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.request(method, path, **kwargs)
        return self.parse(response)

    @staticmethod
    def parse(response: httpx.Response) -> Any:
        if response.status_code == 204:
            return None
        try:
            body: Any = response.json()
        except ValueError:
            body = None

        if response.is_success:
            return body

        message = None
        details = None
        if isinstance(body, dict):
            value = body.get("error")
            if isinstance(value, str) and value.strip():
                message = value.strip()
            details = body.get("details")
        if not message:
            message = DEFAULT_MESSAGES.get(
                response.status_code,
                f"The server returned HTTP {response.status_code}.",
            )
        if response.status_code == 401:
            message = f"{message} Run `graphia login` again."
        raise ApiError(response.status_code, message, details=details)

    def upload_file(
        self,
        url: str,
        headers: dict[str, str],
        path: Path,
        *,
        attempts: int = 3,
    ) -> None:
        data = path.read_bytes()
        merged = dict(headers)
        merged.setdefault("Content-Type", "application/octet-stream")
        if self.verbose:
            print(f"  PUT <storage> ({path.name})", file=sys.stderr)

        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = httpx.put(
                    url,
                    content=data,
                    headers=merged,
                    timeout=120.0,
                )
            except httpx.RequestError as exc:
                last_error = exc
            else:
                if response.is_success:
                    return
                if 400 <= response.status_code < 500:
                    raise ApiError(
                        response.status_code,
                        "Storage rejected the upload. Try the file again.",
                    )
                last_error = ApiError(response.status_code, "Storage rejected the upload.")
            if attempt + 1 < attempts:
                time.sleep(1.0 * (attempt + 1))

        raise NetworkError("Could not upload the file to storage.") from last_error

    def download_file(self, url: str, destination: Path, *, attempts: int = 3) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        part = destination.with_name(destination.name + ".part")
        if self.verbose:
            print(f"  GET <storage> -> {destination}", file=sys.stderr)

        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as response:
                    if response.status_code >= 400:
                        raise ApiError(
                            response.status_code,
                            "Could not download the converted file.",
                        )
                    with part.open("wb") as handle:
                        for chunk in response.iter_bytes():
                            handle.write(chunk)
                os.replace(part, destination)
                return
            except (httpx.RequestError, ApiError, OSError) as exc:
                last_error = exc
                try:
                    part.unlink(missing_ok=True)
                except OSError:
                    pass
            if attempt + 1 < attempts:
                time.sleep(1.0 * (attempt + 1))

        if isinstance(last_error, ApiError):
            raise last_error
        if isinstance(last_error, OSError):
            raise NetworkError(f"Could not write {destination}.") from last_error
        raise NetworkError("Could not download the converted file.") from last_error
