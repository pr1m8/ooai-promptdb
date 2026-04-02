"""SQLAlchemy persistence layer for prompts, versions, aliases, and assets.

This module defines four ORM tables and the :class:`PromptRepository` that
reads and writes them:

- ``prompts`` — logical prompt identity (namespace + name)
- ``prompt_versions`` — immutable version rows (spec JSON, hash, revision)
- ``prompt_aliases`` — movable pointers (``production``, ``staging``, etc.)
- ``prompt_assets`` — relational metadata for blob-backed export artifacts

Versions are **immutable** — once created, a version's spec never changes.
Aliases are **movable** — promoting a version to production is an alias move.

Creating tables and a session factory::

    from promptdb.db import create_all, create_session_factory

    create_all("sqlite:///./promptdb.sqlite3")
    factory = create_session_factory("sqlite:///./promptdb.sqlite3")

Using the repository directly (normally the service does this)::

    with factory() as session:
        repo = PromptRepository(session)
        version = repo.create_version(
            namespace="support", name="triage", spec=spec,
        )
        repo.move_alias(
            namespace="support", name="triage",
            alias="production", version_id=version.id,
        )
        session.commit()
        view = repo.resolve(
            namespace="support", name="triage", selector="production",
        )

Resolution order for selectors:

1. Exact version UUID
2. ``rev:N`` revision number
3. Alias name
4. User-version label
5. ``latest`` fallback (highest revision)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from promptdb.domain import (
    PromptAssetKind,
    PromptAssetView,
    PromptSpec,
    PromptVersionView,
)


class Base(DeclarativeBase):
    """Declarative base.

    Args:
        None.

    Returns:
        Base: Declarative base class.

    Raises:
        None.

    Examples:
        >>> issubclass(Base, DeclarativeBase)
        True
    """


class PromptORM(Base):
    """Logical prompt identity row.

    Args:
        None.

    Returns:
        PromptORM: ORM model.

    Raises:
        None.

    Examples:
        >>> PromptORM(namespace='support', name='triage').namespace
        'support'
    """

    __tablename__ = "prompts"
    __table_args__ = (UniqueConstraint("namespace", "name", name="uq_prompts_namespace_name"),)

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    versions: Mapped[list[PromptVersionORM]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    aliases: Mapped[list[PromptAliasORM]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )


class PromptVersionORM(Base):
    """Immutable prompt version row.

    Args:
        None.

    Returns:
        PromptVersionORM: ORM model.

    Raises:
        None.

    Examples:
        >>> PromptVersionORM(prompt_id='p', revision=1, spec_json='{}', spec_hash='x').revision
        1
    """

    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint(
            "prompt_id",
            "revision",
            name="uq_prompt_versions_prompt_revision",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    prompt_id: Mapped[str] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    user_version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    spec_json: Mapped[str] = mapped_column(Text, nullable=False)
    spec_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    prompt: Mapped[PromptORM] = relationship(back_populates="versions")
    assets: Mapped[list[PromptAssetORM]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
    )


class PromptAliasORM(Base):
    """Alias row.

    Args:
        None.

    Returns:
        PromptAliasORM: ORM model.

    Raises:
        None.

    Examples:
        >>> PromptAliasORM(prompt_id='p', alias='latest', version_id='v').alias
        'latest'
    """

    __tablename__ = "prompt_aliases"
    __table_args__ = (
        UniqueConstraint(
            "prompt_id",
            "alias",
            name="uq_prompt_aliases_prompt_alias",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    prompt_id: Mapped[str] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    version_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    prompt: Mapped[PromptORM] = relationship(back_populates="aliases")


class PromptAssetORM(Base):
    """Relational metadata for blob assets linked to a prompt version.

    Args:
        None.

    Returns:
        PromptAssetORM: ORM model.

    Raises:
        None.

    Examples:
        >>> asset = PromptAssetORM(
        ...     version_id='v', kind='export_bundle',
        ...     storage_backend='local', bucket='promptdb', object_key='x',
        ... )
        >>> asset.object_key
        'x'
    """

    __tablename__ = "prompt_assets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    version_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_backend: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    byte_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    version: Mapped[PromptVersionORM] = relationship(
        back_populates="assets",
    )


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory.

    Args:
        database_url: SQLAlchemy URL.

    Returns:
        sessionmaker[Session]: Session factory.

    Raises:
        None.

    Examples:
        >>> factory = create_session_factory('sqlite:///./promptdb.sqlite3')
        >>> callable(factory)
        True
    """
    engine = create_engine(database_url, future=True)
    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )


def create_all(database_url: str) -> None:
    """Create all database tables.

    Args:
        database_url: SQLAlchemy URL.

    Returns:
        None.

    Raises:
        SQLAlchemyError: If DDL execution fails.

    Examples:
        >>> create_all('sqlite:///./promptdb.sqlite3')
    """
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    engine.dispose()


class PromptRepository:
    """Repository for storing and resolving prompts.

    Args:
        session: SQLAlchemy session.

    Returns:
        PromptRepository: Repository object.

    Raises:
        None.

    Examples:
        .. code-block:: python

            repository = PromptRepository(session)
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_prompt(
        self,
        *,
        namespace: str,
        name: str,
    ) -> PromptORM:
        """Get or create a logical prompt row.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.

        Returns:
            PromptORM: Existing or newly created row.

        Raises:
            SQLAlchemyError: If persistence fails.

        Examples:
            .. code-block:: python

                row = repository.get_or_create_prompt(
                    namespace='support', name='triage',
                )
        """
        row = self.session.scalar(
            select(PromptORM).where(
                PromptORM.namespace == namespace,
                PromptORM.name == name,
            ),
        )
        if row is not None:
            return row
        row = PromptORM(namespace=namespace, name=name)
        self.session.add(row)
        self.session.flush()
        return row

    def create_version(
        self,
        *,
        namespace: str,
        name: str,
        spec: PromptSpec,
        created_by: str | None = None,
    ) -> PromptVersionORM:
        """Create a new immutable prompt version.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.
            spec: Prompt spec.
            created_by: Creator identifier.

        Returns:
            PromptVersionORM: Created version row.

        Raises:
            SQLAlchemyError: If persistence fails.

        Examples:
            .. code-block:: python

                version = repository.create_version(
                    namespace='support', name='triage', spec=spec,
                )
        """
        prompt = self.get_or_create_prompt(
            namespace=namespace,
            name=name,
        )
        revision = self.session.scalar(
            select(func.max(PromptVersionORM.revision)).where(
                PromptVersionORM.prompt_id == prompt.id,
            ),
        )
        next_revision = int(revision or 0) + 1
        if spec.metadata.user_version is not None:
            duplicate = self.session.scalar(
                select(PromptVersionORM).where(
                    PromptVersionORM.prompt_id == prompt.id,
                    PromptVersionORM.user_version == spec.metadata.user_version,
                ),
            )
            if duplicate is not None:
                uv = spec.metadata.user_version
                raise ValueError(
                    f"Prompt {namespace}/{name} already has user_version '{uv}'.",
                )
        spec_json = spec.model_dump_json(exclude_computed_fields=True)
        spec_hash = hashlib.sha256(
            spec_json.encode("utf-8"),
        ).hexdigest()
        row = PromptVersionORM(
            prompt_id=prompt.id,
            revision=next_revision,
            user_version=spec.metadata.user_version,
            spec_json=spec_json,
            spec_hash=spec_hash,
            created_by=created_by,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def create_asset(
        self,
        *,
        version_id: str,
        kind: PromptAssetKind,
        storage_backend: str,
        bucket: str,
        object_key: str,
        content_type: str | None = None,
        byte_size: int | None = None,
        checksum_sha256: str | None = None,
        metadata_json: dict[str, str] | None = None,
    ) -> PromptAssetORM:
        """Create a relational asset row linked to a prompt version."""
        row = PromptAssetORM(
            version_id=version_id,
            kind=kind.value,
            storage_backend=storage_backend,
            bucket=bucket,
            object_key=object_key,
            content_type=content_type,
            byte_size=byte_size,
            checksum_sha256=checksum_sha256,
            metadata_json=json.dumps(metadata_json or {}),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_assets(
        self,
        *,
        version_id: str,
    ) -> list[PromptAssetView]:
        """List blob assets linked to a prompt version."""
        rows = list(
            self.session.scalars(
                select(PromptAssetORM)
                .where(PromptAssetORM.version_id == version_id)
                .order_by(PromptAssetORM.created_at.desc()),
            ),
        )
        return [
            PromptAssetView(
                asset_id=row.id,
                version_id=row.version_id,
                kind=PromptAssetKind(row.kind),
                storage_backend=row.storage_backend,
                bucket=row.bucket,
                object_key=row.object_key,
                content_type=row.content_type,
                byte_size=row.byte_size,
                checksum_sha256=row.checksum_sha256,
                metadata_json=json.loads(row.metadata_json or "{}"),
                created_at=(row.created_at.isoformat() if row.created_at else None),
            )
            for row in rows
        ]

    def move_alias(
        self,
        *,
        namespace: str,
        name: str,
        alias: str,
        version_id: str,
    ) -> PromptAliasORM:
        """Move an alias to a concrete version.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.
            alias: Alias name.
            version_id: Target version id.

        Returns:
            PromptAliasORM: Alias row.

        Raises:
            LookupError: If the prompt is missing.

        Examples:
            .. code-block:: python

                repository.move_alias(
                    namespace='support', name='triage',
                    alias='production', version_id='...',
                )
        """
        prompt = self.session.scalar(
            select(PromptORM).where(
                PromptORM.namespace == namespace,
                PromptORM.name == name,
            ),
        )
        if prompt is None:
            raise LookupError(f"Unknown prompt: {namespace}/{name}")
        row = self.session.scalar(
            select(PromptAliasORM).where(
                PromptAliasORM.prompt_id == prompt.id,
                PromptAliasORM.alias == alias,
            ),
        )
        if row is None:
            row = PromptAliasORM(
                prompt_id=prompt.id,
                alias=alias,
                version_id=version_id,
            )
            self.session.add(row)
        else:
            row.version_id = version_id
        self.session.flush()
        return row

    def resolve(
        self,
        *,
        namespace: str,
        name: str,
        selector: str,
    ) -> PromptVersionView:
        """Resolve a selector into a prompt version.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.
            selector: Alias, user-facing version label, or version id.

        Returns:
            PromptVersionView: Resolved prompt version.

        Raises:
            LookupError: If resolution fails.

        Examples:
            .. code-block:: python

                view = repository.resolve(
                    namespace='support', name='triage',
                    selector='latest',
                )
        """
        prompt = self.session.scalar(
            select(PromptORM).where(
                PromptORM.namespace == namespace,
                PromptORM.name == name,
            ),
        )
        if prompt is None:
            raise LookupError(f"Unknown prompt: {namespace}/{name}")
        version = self.session.scalar(
            select(PromptVersionORM).where(
                PromptVersionORM.id == selector,
                PromptVersionORM.prompt_id == prompt.id,
            ),
        )
        if version is None and selector.startswith("rev:"):
            revision_value = selector.removeprefix("rev:")
            if revision_value.isdigit():
                version = self.session.scalar(
                    select(PromptVersionORM).where(
                        PromptVersionORM.prompt_id == prompt.id,
                        PromptVersionORM.revision == int(revision_value),
                    ),
                )
        if version is None:
            alias_row = self.session.scalar(
                select(PromptAliasORM).where(
                    PromptAliasORM.prompt_id == prompt.id,
                    PromptAliasORM.alias == selector,
                ),
            )
            if alias_row is not None:
                version = self.session.scalar(
                    select(PromptVersionORM).where(
                        PromptVersionORM.id == alias_row.version_id,
                    ),
                )
        if version is None:
            version = self.session.scalar(
                select(PromptVersionORM).where(
                    PromptVersionORM.prompt_id == prompt.id,
                    PromptVersionORM.user_version == selector,
                ),
            )
        if version is None and selector == "latest":
            version = self.session.scalar(
                select(PromptVersionORM)
                .where(PromptVersionORM.prompt_id == prompt.id)
                .order_by(PromptVersionORM.revision.desc())
                .limit(1),
            )
        if version is None:
            raise LookupError(
                f"Unable to resolve selector '{selector}' for {namespace}/{name}",
            )
        aliases = list(
            self.session.scalars(
                select(PromptAliasORM.alias).where(
                    PromptAliasORM.prompt_id == prompt.id,
                    PromptAliasORM.version_id == version.id,
                ),
            ),
        )
        return PromptVersionView(
            version_id=version.id,
            namespace=prompt.namespace,
            name=prompt.name,
            revision=version.revision,
            user_version=version.user_version,
            spec=PromptSpec.model_validate_json(version.spec_json),
            created_by=version.created_by,
            created_at=version.created_at,
            aliases=aliases,
            assets=self.list_assets(version_id=version.id),
        )

    def list_versions(self) -> list[PromptVersionView]:
        """List all known prompt versions.

        Args:
            None.

        Returns:
            list[PromptVersionView]: Version views.

        Raises:
            None.

        Examples:
            .. code-block:: python

                rows = repository.list_versions()
        """
        rows = self.session.execute(
            select(PromptVersionORM, PromptORM)
            .join(PromptORM, PromptORM.id == PromptVersionORM.prompt_id)
            .order_by(
                PromptORM.namespace,
                PromptORM.name,
                PromptVersionORM.revision.desc(),
            ),
        ).all()
        results: list[PromptVersionView] = []
        for version, prompt in rows:
            aliases = list(
                self.session.scalars(
                    select(PromptAliasORM.alias).where(
                        PromptAliasORM.prompt_id == prompt.id,
                        PromptAliasORM.version_id == version.id,
                    ),
                ),
            )
            results.append(
                PromptVersionView(
                    version_id=version.id,
                    namespace=prompt.namespace,
                    name=prompt.name,
                    revision=version.revision,
                    user_version=version.user_version,
                    spec=PromptSpec.model_validate_json(
                        version.spec_json,
                    ),
                    created_by=version.created_by,
                    created_at=version.created_at,
                    aliases=aliases,
                    assets=self.list_assets(version_id=version.id),
                ),
            )
        return results
