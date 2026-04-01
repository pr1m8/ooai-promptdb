"""Service layer for :mod:`promptdb`.

Purpose:
    Provide high-level workflows across persistence and storage adapters.

Design:
    The service owns alias movement, registration, resolution, rendering, and
    export logic so both the API and CLI can share it.

Attributes:
    PromptService: High-level service class.

Examples:
    .. code-block:: python

        service = PromptService(session_factory, blob_store)
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from promptdb.db import PromptRepository
from promptdb.domain import (
    PromptAssetKind,
    PromptAssetView,
    PromptRef,
    PromptRegistration,
    PromptRenderResult,
    PromptVersionView,
)
from promptdb.storage import LocalBlobStore, MinioBlobStore, object_metadata

BlobStore = LocalBlobStore | MinioBlobStore


class PromptService:
    """Application service for prompt workflows.

    Args:
        session_factory: SQLAlchemy session factory.
        blob_store: Storage adapter with ``put_text`` and ``get_text``.

    Returns:
        PromptService: Service object.

    Raises:
        None.

    Examples:
        .. code-block:: python

            service = PromptService(session_factory, blob_store)
    """

    def __init__(self, session_factory: sessionmaker[Session], blob_store: BlobStore) -> None:
        self.session_factory = session_factory
        self.blob_store = blob_store

    def register(self, registration: PromptRegistration) -> PromptVersionView:
        """Register a new immutable prompt version.

        Args:
            registration: Registration payload.

        Returns:
            PromptVersionView: Created version.

        Raises:
            SQLAlchemyError: If persistence fails.

        Examples:
            .. code-block:: python

                version = service.register(registration)
        """
        with self.session_factory() as session:
            repository = PromptRepository(session)
            version = repository.create_version(
                namespace=registration.namespace,
                name=registration.name,
                spec=registration.spec,
                created_by=registration.created_by,
            )
            if registration.alias:
                repository.move_alias(
                    namespace=registration.namespace,
                    name=registration.name,
                    alias=registration.alias,
                    version_id=version.id,
                )
            session.commit()
            return repository.resolve(
                namespace=registration.namespace,
                name=registration.name,
                selector=version.id,
            )

    def move_alias(
        self,
        *,
        namespace: str,
        name: str,
        alias: str,
        version_id: str,
    ) -> PromptVersionView:
        """Move an alias and return the target version.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.
            alias: Alias name.
            version_id: Target version id.

        Returns:
            PromptVersionView: Target version.

        Raises:
            LookupError: If the prompt is missing.

        Examples:
            .. code-block:: python

                view = service.move_alias(
                    namespace='support', name='triage',
                    alias='production', version_id='...',
                )
        """
        with self.session_factory() as session:
            repository = PromptRepository(session)
            repository.move_alias(
                namespace=namespace, name=name, alias=alias, version_id=version_id
            )
            session.commit()
            return repository.resolve(namespace=namespace, name=name, selector=version_id)

    def resolve(self, ref: PromptRef) -> PromptVersionView:
        """Resolve a prompt reference.

        Args:
            ref: Prompt reference.

        Returns:
            PromptVersionView: Resolved version.

        Raises:
            LookupError: If resolution fails.

        Examples:
            .. code-block:: python

                view = service.resolve(PromptRef(namespace='support', name='triage'))
        """
        with self.session_factory() as session:
            repository = PromptRepository(session)
            return repository.resolve(namespace=ref.namespace, name=ref.name, selector=ref.selector)

    def render(self, ref: PromptRef, variables: dict[str, object]) -> PromptRenderResult:
        """Resolve and render a prompt.

        Args:
            ref: Prompt reference.
            variables: Runtime variables.

        Returns:
            PromptRenderResult: Rendered output.

        Raises:
            LookupError: If resolution fails.

        Examples:
            .. code-block:: python

                ref = PromptRef(namespace='support', name='triage')
                result = service.render(ref, {'question': 'hello'})
        """
        version = self.resolve(ref)
        return version.render(variables)

    def list_versions(self) -> list[PromptVersionView]:
        """List all known versions.

        Args:
            None.

        Returns:
            list[PromptVersionView]: Version views.

        Raises:
            None.

        Examples:
            .. code-block:: python

                versions = service.list_versions()
        """
        with self.session_factory() as session:
            return PromptRepository(session).list_versions()

    def export_bundle(
        self, version: PromptVersionView, *, key_prefix: str = "exports"
    ) -> PromptAssetView:
        """Export a prompt version bundle to blob storage.

        Args:
            version: Prompt version to export.
            key_prefix: Storage key prefix.

        Returns:
            PromptAssetView: Relational asset view linked to the stored blob.

        Raises:
            OSError: If writing fails.

        Examples:
            .. code-block:: python

                key = service.export_bundle(version)
        """
        key = f"{key_prefix}/{version.namespace}/{version.name}/{version.version_id}.json"
        payload = version.model_dump_json(indent=2)
        self.blob_store.put_text(key, payload)
        meta = object_metadata(
            self.blob_store, key, content=payload, content_type="application/json"
        )
        with self.session_factory() as session:
            repository = PromptRepository(session)
            byte_size = meta["byte_size"]
            checksum = meta["checksum_sha256"]
            repository.create_asset(
                version_id=version.version_id,
                kind=PromptAssetKind.EXPORT_BUNDLE,
                storage_backend=str(meta["storage_backend"]),
                bucket=str(meta["bucket"]),
                object_key=str(meta["object_key"]),
                content_type="application/json",
                byte_size=int(byte_size) if isinstance(byte_size, int) else None,
                checksum_sha256=str(checksum) if checksum is not None else None,
                metadata_json={
                    "namespace": version.namespace,
                    "name": version.name,
                    "revision": str(version.revision),
                },
            )
            session.commit()
            assets = repository.list_assets(version_id=version.version_id)
        return assets[0]

    def list_assets(self, ref: PromptRef) -> list[PromptAssetView]:
        """List relational blob assets for a resolved prompt version.

        Args:
            ref: Prompt reference.

        Returns:
            list[PromptAssetView]: Linked asset metadata.

        Raises:
            LookupError: If the prompt cannot be resolved.
        """
        version = self.resolve(ref)
        with self.session_factory() as session:
            return PromptRepository(session).list_assets(version_id=version.version_id)

    def export_to_file(self, version: PromptVersionView, path: str | Path) -> Path:
        """Export a prompt version to a local JSON file.

        Args:
            version: Prompt version.
            path: Output path.

        Returns:
            Path: Output path.

        Raises:
            OSError: If writing fails.

        Examples:
            .. code-block:: python

                service.export_to_file(version, 'build/version.json')
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(version.model_dump_json(indent=2), encoding="utf-8")
        return output_path
