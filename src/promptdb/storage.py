"""Blob storage adapters for :mod:`promptdb`.

Purpose:
    Provide local filesystem and MinIO-backed blob storage adapters for prompt
    exports and related artifacts.

Design:
    The local adapter is fully runnable in tests. The MinIO adapter imports the
    official MinIO client lazily.

Attributes:
    LocalBlobStore: Filesystem-backed blob store.
    MinioBlobStore: MinIO-backed blob store.

Examples:
    >>> store = LocalBlobStore('.tmp-blobs')
    >>> key = store.put_text('demo.txt', 'hello')
    >>> store.get_text(key)
    'hello'
"""

from __future__ import annotations

import datetime as dt
from io import BytesIO
from pathlib import Path


class LocalBlobStore:
    """Filesystem-backed blob store.

    Args:
        root: Storage root directory.

    Returns:
        LocalBlobStore: Storage adapter.

    Raises:
        None.

    Examples:
        >>> store = LocalBlobStore('.tmp-blobs')
        >>> store.put_text('x.txt', 'x')
        'x.txt'
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.backend_name = "local"
        self.bucket_name = str(self.root)

    def _path(self, key: str | object) -> Path:
        """Resolve an object key to a filesystem path.

        Args:
            key: Relative object key.

        Returns:
            Path: Concrete path.

        Raises:
            None.

        Examples:
            >>> LocalBlobStore('.tmp-blobs')._path('x.txt').name
            'x.txt'
        """
        actual_key = getattr(key, "object_key", key)
        return self.root / str(actual_key)

    def put_text(self, key: str, content: str) -> str:
        """Store text content.

        Args:
            key: Object key.
            content: Text payload.

        Returns:
            str: Stored object key.

        Raises:
            OSError: If writing fails.

        Examples:
            >>> LocalBlobStore('.tmp-blobs').put_text('x.txt', 'hello')
            'x.txt'
        """
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return key

    def get_text(self, key: str) -> str:
        """Read text content.

        Args:
            key: Object key.

        Returns:
            str: Stored content.

        Raises:
            FileNotFoundError: If the key does not exist.

        Examples:
            >>> store = LocalBlobStore('.tmp-blobs')
            >>> _ = store.put_text('x.txt', 'hello')
            >>> store.get_text('x.txt')
            'hello'
        """
        return self._path(key).read_text(encoding="utf-8")

    def presign_upload(self, key: str, *, expires_seconds: int = 3600) -> str:
        """Return a pseudo upload URL for local usage.

        Args:
            key: Object key.
            expires_seconds: Ignored expiration horizon.

        Returns:
            str: ``file://`` URL.

        Raises:
            None.

        Examples:
            >>> LocalBlobStore('.tmp-blobs').presign_upload('x.txt').startswith('file://')
            True
        """
        del expires_seconds
        return self._path(key).resolve().as_uri()


class MinioBlobStore:
    """MinIO-backed blob store.

    Args:
        endpoint: MinIO endpoint.
        access_key: Access key.
        secret_key: Secret key.
        bucket: Bucket name.
        secure: Whether to use TLS.

    Returns:
        MinioBlobStore: Storage adapter.

    Raises:
        ImportError: If the MinIO package is unavailable.

    Examples:
        .. code-block:: python

            store = MinioBlobStore(
                endpoint='localhost:9000',
                access_key='minioadmin',
                secret_key='minioadmin',
                bucket='promptdb',
                secure=False,
            )
    """

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        try:
            from minio import Minio
        except ImportError as exc:
            raise ImportError("Install the 'minio' extra to use MinioBlobStore.") from exc
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket
        self.backend_name = "minio"
        self.bucket_name = bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def put_text(self, key: str, content: str) -> str:
        """Upload text content.

        Args:
            key: Object key.
            content: Text payload.

        Returns:
            str: Stored object key.

        Raises:
            S3Error: If upload fails.

        Examples:
            .. code-block:: python

                store.put_text('exports/demo.txt', 'hello')
        """
        payload = content.encode("utf-8")
        self.client.put_object(
            self.bucket,
            key,
            BytesIO(payload),
            len(payload),
            content_type="text/plain; charset=utf-8",
        )
        return key

    def get_text(self, key: str) -> str:
        """Download text content.

        Args:
            key: Object key.

        Returns:
            str: Text payload.

        Raises:
            S3Error: If download fails.

        Examples:
            .. code-block:: python

                body = store.get_text('exports/demo.txt')
        """
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()

    def presign_upload(self, key: str, *, expires_seconds: int = 3600) -> str:
        """Generate a presigned PUT URL.

        Args:
            key: Object key.
            expires_seconds: Expiration horizon.

        Returns:
            str: Presigned URL.

        Raises:
            S3Error: If URL generation fails.

        Examples:
            .. code-block:: python

                url = store.presign_upload('exports/demo.txt')
        """
        return self.client.presigned_put_object(
            self.bucket,
            key,
            expires=dt.timedelta(seconds=expires_seconds),
        )


def object_metadata(
    store: object,
    key: str,
    *,
    content: str | None = None,
    content_type: str | None = None,
) -> dict[str, object]:
    """Build relational metadata for a stored blob object.

    Args:
        store: Blob store adapter.
        key: Stored object key.
        content: Optional content used to estimate size and checksum.
        content_type: Optional MIME type.

    Returns:
        dict[str, object]: Metadata payload for relational persistence.

    Raises:
        None.

    Examples:
        >>> meta = object_metadata(LocalBlobStore('.tmp-blobs'), 'x.txt', content='hello')
        >>> meta['storage_backend']
        'local'
    """
    import hashlib

    payload = content.encode("utf-8") if content is not None else None
    checksum = hashlib.sha256(payload).hexdigest() if payload is not None else None
    return {
        "storage_backend": getattr(store, "backend_name", store.__class__.__name__.lower()),
        "bucket": getattr(store, "bucket_name", ""),
        "object_key": key,
        "content_type": content_type,
        "byte_size": len(payload) if payload is not None else None,
        "checksum_sha256": checksum,
    }
