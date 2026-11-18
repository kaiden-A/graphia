from __future__ import annotations


class GraphiaError(Exception):
    """A user-facing error. The CLI prints the message and exits non-zero."""


class UsageError(GraphiaError):
    pass


class AuthError(GraphiaError):
    pass


class NetworkError(GraphiaError):
    pass


class RateLimitError(GraphiaError):
    pass


class ApiError(GraphiaError):
    def __init__(
        self,
        status: int,
        message: str,
        *,
        details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.details = details


class BatchCancelled(Exception):
    """Internal signal used to stop scheduled work after a fatal error."""
