from __future__ import annotations

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Graphia"
    app_env: str = "development"
    log_level: str = "INFO"

    app_secret: str = "dev-only-change-me"
    database_url: str = "postgresql+pg8000://postgres:postgres@localhost:5432/graphia"
    db_schema: str = "public"

    session_cookie_name: str = "graphia_session"
    session_ttl_days: int = 30
    cookie_secure: bool = False

    signup_enabled: bool = True
    signup_invite_code: str = ""

    r2_account_id: str = ""
    r2_endpoint: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "graphia"
    r2_region: str = "auto"

    processor_url: str = "http://localhost:8001"
    internal_token: str = "dev-internal-token-change-me"

    max_upload_mb: int = 25
    max_active_jobs_per_user: int = 3
    uploads_per_hour_per_ip: int = 20
    daily_job_limit: int = 200
    job_expiry_hours: int = 24
    upload_url_ttl_seconds: int = 600
    download_url_ttl_seconds: int = 300

    processor_max_workers: int = 1
    conversion_timeout_seconds: int = 300
    soffice_bin: str = "soffice"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def session_ttl_seconds(self) -> int:
        return self.session_ttl_days * 24 * 60 * 60

    @property
    def signup_requires_code(self) -> bool:
        return bool(self.signup_invite_code.strip())

    @property
    def sqlalchemy_url(self) -> str:
        """Normalize common Postgres URLs for pg8000 and drop libpq-only options."""
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+pg8000://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+pg8000://" + url[len("postgresql://") :]

        if not url.startswith("postgresql+pg8000://"):
            return url

        parts = urlsplit(url)
        blocked = {
            "sslmode",
            "channel_binding",
            "sslcert",
            "sslkey",
            "sslrootcert",
            "sslcrl",
            "sslpassword",
        }
        query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key not in blocked
        ]
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

    @property
    def ssl_required(self) -> bool:
        return "sslmode=require" in self.database_url or "sslmode=verify" in self.database_url

    @property
    def r2_endpoint_url(self) -> str:
        if self.r2_endpoint.strip():
            return self.r2_endpoint.strip().rstrip("/")
        if self.r2_account_id.strip():
            return f"https://{self.r2_account_id.strip()}.r2.cloudflarestorage.com"
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
