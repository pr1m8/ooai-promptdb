"""Environment-backed application configuration.

All settings are read from ``PROMPTDB_*`` environment variables via
Pydantic Settings. The defaults work for local development with SQLite and
local blob storage — no external services required.

Environment variables:

- ``PROMPTDB_DATABASE_URL`` — SQLAlchemy URL (default: ``sqlite:///./promptdb.sqlite3``)
- ``PROMPTDB_BLOB_ROOT`` — local blob directory (default: ``.blobs``)
- ``PROMPTDB_STORAGE_BACKEND`` — ``local`` or ``minio`` (default: ``local``)
- ``PROMPTDB_API_PREFIX`` — API route prefix (default: ``/api/v1``)
- ``PROMPTDB_MINIO_ENDPOINT`` — MinIO host:port (required if ``minio``)
- ``PROMPTDB_MINIO_ACCESS_KEY`` — MinIO access key
- ``PROMPTDB_MINIO_SECRET_KEY`` — MinIO secret key
- ``PROMPTDB_MINIO_BUCKET`` — MinIO bucket (default: ``promptdb``)
- ``PROMPTDB_ENABLE_METRICS`` — mount Prometheus ``/metrics`` (default: false)
- ``PROMPTDB_ENABLE_OTEL`` — enable OpenTelemetry instrumentation (default: false)
- ``PROMPTDB_LOG_LEVEL`` — root log level (default: ``INFO``)

Usage::

    from promptdb.settings import AppSettings

    settings = AppSettings()                          # from env vars
    settings = AppSettings(database_url="sqlite:///:memory:")  # explicit
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Environment-backed application settings.

    Args:
        database_url: SQLAlchemy database URL.
        blob_root: Local blob storage root.
        storage_backend: ``local`` or ``minio``.
        api_prefix: API route prefix.
        service_name: Service name for logs and traces.
        enable_metrics: Whether to expose metrics.
        enable_otel: Whether to enable OTel wiring.
        redis_url: Optional Redis URL.
        minio_endpoint: MinIO endpoint.
        minio_access_key: MinIO access key.
        minio_secret_key: MinIO secret key.
        minio_bucket: MinIO bucket.
        minio_secure: Whether MinIO uses TLS.
        log_level: Root log level.

    Returns:
        AppSettings: Loaded settings instance.

    Raises:
        None.

    Examples:
        >>> AppSettings(database_url="sqlite:///./x.sqlite3").storage_backend
        'local'
    """

    model_config = SettingsConfigDict(env_prefix="PROMPTDB_", extra="ignore")

    database_url: str = "sqlite:///./promptdb.sqlite3"
    blob_root: str = ".blobs"
    storage_backend: str = "local"
    api_prefix: str = "/api/v1"
    service_name: str = "promptdb-api"
    enable_metrics: bool = False
    enable_otel: bool = False
    redis_url: str | None = None
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str = "promptdb"
    minio_secure: bool = False
    log_level: str = Field(default="INFO")
