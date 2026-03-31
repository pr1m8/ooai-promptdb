"""Application settings for :mod:`promptdb`.

Purpose:
    Centralize environment-backed configuration for the API, database, storage,
    and observability layers.

Design:
    The settings model reads environment variables only. Adapters and services
    are constructed elsewhere.

Attributes:
    AppSettings: Typed settings model.

Examples:
    >>> AppSettings(database_url="sqlite:///./promptdb.sqlite3").api_prefix
    '/api/v1'
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
