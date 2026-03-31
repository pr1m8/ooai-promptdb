"""High-level ergonomic client APIs for :mod:`promptdb`.

Purpose:
    Expose a compact, developer-friendly interface for registering, resolving,
    rendering, and exporting prompts without forcing callers to manually build
    service payloads.

Design:
    The client is intentionally local-first and wraps :class:`~promptdb.service.PromptService`.
    It supports compact prompt references, file-based registration, and a rich
    ``ResolvedPrompt`` wrapper for materialization and rendering.

Attributes:
    PromptClient: Main local client facade.

Examples:
    .. code-block:: python

        from promptdb import PromptClient, PromptKind

        client = PromptClient.from_env()
        version = client.register_text(
            namespace="support",
            name="triage",
            template="Hello {name}",
            kind=PromptKind.STRING,
            alias="production",
        )
        resolved = client.get("support/triage:production")
        assert resolved.render_text({"name": "Will"}) == "Hello Will"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from promptdb.api import build_service
from promptdb.db import create_all
from promptdb.domain import (
    ChatMessage,
    MessageRole,
    PromptKind,
    PromptMetadata,
    PromptRef,
    PromptRegistration,
    PromptSpec,
    PromptVersionView,
    ResolvedPrompt,
    TemplateFormat,
)
from promptdb.files import load_prompt_file, write_version_bundle
from promptdb.service import PromptService
from promptdb.settings import AppSettings


class PromptClient:
    """Developer-friendly facade over :class:`~promptdb.service.PromptService`.

    Args:
        service: Prompt service instance.

    Returns:
        PromptClient: Local prompt client.

    Raises:
        None.

    Examples:
        .. code-block:: python

            client = PromptClient.from_env()
            resolved = client.get("support/triage:latest")
    """

    def __init__(self, service: PromptService) -> None:
        """Initialize the client with a prompt service instance."""
        self.service = service

    @classmethod
    def from_env(cls, settings: AppSettings | None = None) -> PromptClient:
        """Create a client from environment-backed settings.

        Args:
            settings: Optional explicit settings.

        Returns:
            PromptClient: Configured client.

        Raises:
            ValueError: If the storage backend is misconfigured.

        Examples:
            >>> settings = AppSettings(database_url='sqlite:///:memory:')
            >>> isinstance(PromptClient.from_env(settings), PromptClient)
            True
        """
        resolved_settings = settings or AppSettings()
        create_all(resolved_settings.database_url)
        return cls(build_service(resolved_settings))

    @staticmethod
    def _coerce_ref(ref: PromptRef | str) -> PromptRef:
        """Normalize a prompt reference value.

        Args:
            ref: Prompt reference model or compact reference string.

        Returns:
            PromptRef: Normalized prompt reference.

        Raises:
            ValueError: If the string cannot be parsed.

        Examples:
            >>> PromptClient._coerce_ref('support/triage:latest').selector
            'latest'
        """
        if isinstance(ref, PromptRef):
            return ref
        return PromptRef.parse(ref)

    def register_spec(
        self,
        *,
        namespace: str,
        name: str,
        spec: PromptSpec,
        created_by: str | None = None,
        alias: str | None = "latest",
    ) -> PromptVersionView:
        """Register a prompt spec.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.
            spec: Prompt specification.
            created_by: Optional creator identifier.
            alias: Alias to move after creation.

        Returns:
            PromptVersionView: Stored prompt version.

        Raises:
            LookupError: If alias movement fails.

        Examples:
            .. code-block:: python

                version = client.register_spec(namespace='support', name='triage', spec=spec)
        """
        return self.service.register(
            PromptRegistration(
                namespace=namespace,
                name=name,
                spec=spec,
                created_by=created_by,
                alias=alias,
            )
        )

    def register_text(
        self,
        *,
        namespace: str,
        name: str,
        template: str,
        kind: PromptKind = PromptKind.STRING,
        alias: str | None = "latest",
        created_by: str | None = None,
        metadata: PromptMetadata | None = None,
        template_format: TemplateFormat = TemplateFormat.FSTRING,
        partial_variables: dict[str, Any] | None = None,
        role: MessageRole = MessageRole.HUMAN,
    ) -> PromptVersionView:
        """Register a prompt directly from text.

        Args:
            namespace: Prompt namespace.
            name: Prompt name.
            template: Root template or message template.
            kind: Prompt kind.
            alias: Alias to move after registration.
            created_by: Optional creator identifier.
            metadata: Optional prompt metadata.
            template_format: Template engine.
            partial_variables: Stored partial variables.
            role: Chat role when ``kind`` is ``chat``.

        Returns:
            PromptVersionView: Stored prompt version.

        Raises:
            ValueError: If the prompt shape is invalid.

        Examples:
            .. code-block:: python

                version = client.register_text(
                    namespace='support',
                    name='triage',
                    template='Hello {name}',
                )
        """
        if kind is PromptKind.STRING:
            spec = PromptSpec(
                kind=kind,
                template=template,
                template_format=template_format,
                partial_variables=partial_variables or {},
                metadata=metadata or PromptMetadata(title=name),
            )
        else:
            spec = PromptSpec(
                kind=kind,
                messages=[ChatMessage(role=role, template=template)],
                template_format=template_format,
                partial_variables=partial_variables or {},
                metadata=metadata or PromptMetadata(title=name),
            )
        return self.register_spec(
            namespace=namespace,
            name=name,
            spec=spec,
            created_by=created_by,
            alias=alias,
        )

    def register_file(
        self,
        *,
        path: str | Path,
        namespace: str,
        name: str,
        kind: PromptKind | None = None,
        alias: str | None = "latest",
        created_by: str | None = None,
        message_role: MessageRole = MessageRole.HUMAN,
        user_version: str | None = None,
    ) -> PromptVersionView:
        """Register a prompt from a text or structured file.

        Args:
            path: Input file path.
            namespace: Prompt namespace.
            name: Prompt name.
            kind: Prompt kind for plain-text files. Ignored for structured spec files.
            alias: Alias to move after registration.
            created_by: Optional creator identifier.
            message_role: Chat role for plain-text chat prompt files.
            user_version: Optional user-facing version label override.

        Returns:
            PromptVersionView: Stored prompt version.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If ``kind`` is omitted for plain-text files.

        Examples:
            .. code-block:: python

                version = client.register_file(
                    path='prompts/triage.yaml',
                    namespace='support',
                    name='triage',
                )
        """
        spec = load_prompt_file(path, kind=kind, message_role=message_role)
        if user_version is not None:
            spec.metadata.user_version = user_version
        if spec.metadata.title is None:
            spec.metadata.title = name
        return self.register_spec(
            namespace=namespace,
            name=name,
            spec=spec,
            created_by=created_by,
            alias=alias,
        )

    def resolve(self, ref: PromptRef | str) -> PromptVersionView:
        """Resolve a prompt reference.

        Args:
            ref: Prompt reference or compact string.

        Returns:
            PromptVersionView: Resolved prompt version.

        Raises:
            LookupError: If resolution fails.

        Examples:
            >>> client = PromptClient.from_env(AppSettings(database_url='sqlite:///:memory:'))
            >>> version = client.register_text(namespace='x', name='y', template='Hi {name}')
            >>> client.resolve('x/y:latest').version_id == version.version_id
            True
        """
        return self.service.resolve(self._coerce_ref(ref))

    def get(self, ref: PromptRef | str) -> ResolvedPrompt:
        """Resolve and wrap a prompt reference.

        Args:
            ref: Prompt reference or compact string.

        Returns:
            ResolvedPrompt: Wrapped resolved prompt.

        Raises:
            LookupError: If resolution fails.

        Examples:
            >>> client = PromptClient.from_env(AppSettings(database_url='sqlite:///:memory:'))
            >>> _ = client.register_text(namespace='x', name='y', template='Hi {name}')
            >>> client.get('x/y:latest').render_text({'name': 'Will'})
            'Hi Will'
        """
        return self.resolve(ref).wrap()

    def render(self, ref: PromptRef | str, variables: dict[str, Any]) -> Any:
        """Render a prompt reference directly.

        Args:
            ref: Prompt reference or compact string.
            variables: Runtime variables.

        Returns:
            Any: Render result model.

        Raises:
            LookupError: If resolution fails.

        Examples:
            >>> client = PromptClient.from_env(AppSettings(database_url='sqlite:///:memory:'))
            >>> _ = client.register_text(namespace='x', name='y', template='Hi {name}')
            >>> client.render('x/y:latest', {'name': 'Will'}).text
            'Hi Will'
        """
        return self.service.render(self._coerce_ref(ref), variables)

    def list_versions(self) -> list[PromptVersionView]:
        """List all stored versions.

        Args:
            None.

        Returns:
            list[PromptVersionView]: Stored prompt versions.

        Raises:
            None.

        Examples:
            >>> client = PromptClient.from_env(AppSettings(database_url='sqlite:///:memory:'))
            >>> client.list_versions()
            []
        """
        return self.service.list_versions()

    def export_to_file(self, ref: PromptRef | str, path: str | Path) -> Path:
        """Resolve and export a version bundle to a file.

        Args:
            ref: Prompt reference or compact string.
            path: Output file path.

        Returns:
            Path: Written file path.

        Raises:
            LookupError: If resolution fails.
            OSError: If writing fails.

        Examples:
            .. code-block:: python

                client.export_to_file('support/triage:production', 'build/triage.json')
        """
        return write_version_bundle(self.resolve(ref), path)

    def export_file(self, ref: PromptRef | str, path: str | Path) -> Path:
        """Resolve and export a version bundle to a file.

        Args:
            ref: Prompt reference or compact string.
            path: Output file path.

        Returns:
            Path: Written file path.

        Raises:
            LookupError: If resolution fails.
            OSError: If writing fails.

        Examples:
            .. code-block:: python

                client.export_file('support/triage:production', 'build/triage.json')
        """
        return self.export_to_file(ref, path)
