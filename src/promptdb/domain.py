"""Domain models for :mod:`promptdb`.

Purpose:
    Define the prompt schema, metadata, references, version views, and render
    results used by the package.

Design:
    :class:`PromptSpec` is the central abstraction. It supports both string and
    chat prompts, message placeholders, partial variables, and a lightweight
    few-shot block.

Attributes:
    PromptSpec: Main prompt definition model.
    PromptMetadata: Dashboard- and API-friendly metadata.
    PromptVersionView: Immutable view over a stored prompt version.

Examples:
    >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hello {name}")
    >>> spec.render_text({"name": "Will"})
    'Hello Will'
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from enum import StrEnum
from string import Formatter
from typing import Any

from jinja2 import Environment, StrictUndefined
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class PromptKind(StrEnum):
    """Supported prompt kinds.

    Args:
        None.

    Returns:
        PromptKind: Enumeration members for prompt families.

    Raises:
        None.

    Examples:
        >>> PromptKind.CHAT.value
        'chat'
    """

    STRING = "string"
    CHAT = "chat"


class TemplateFormat(StrEnum):
    """Supported template formats.

    Args:
        None.

    Returns:
        TemplateFormat: Enumeration members for supported renderers.

    Raises:
        None.

    Examples:
        >>> TemplateFormat.MUSTACHE.value
        'mustache'
    """

    FSTRING = "f-string"
    JINJA2 = "jinja2"
    MUSTACHE = "mustache"


class PromptAssetKind(StrEnum):
    """Kinds of relational asset records linked to a prompt version.

    Args:
        None.

    Returns:
        PromptAssetKind: Enumeration members for persisted asset categories.

    Raises:
        None.

    Examples:
        >>> PromptAssetKind.EXPORT_BUNDLE.value
        'export_bundle'
    """

    EXPORT_BUNDLE = "export_bundle"
    ATTACHMENT = "attachment"
    EXAMPLE_DATASET = "example_dataset"
    SNAPSHOT = "snapshot"


class MessageRole(StrEnum):
    """Supported chat message roles.

    Args:
        None.

    Returns:
        MessageRole: Enumeration members for message roles.

    Raises:
        None.

    Examples:
        >>> MessageRole.SYSTEM.value
        'system'
    """

    SYSTEM = "system"
    HUMAN = "human"
    AI = "ai"
    GENERIC = "generic"


class PromptMetadata(BaseModel):
    """Rich metadata attached to a prompt version.

    Args:
        title: Human-friendly title.
        description: Longer description.
        tags: Search tags.
        owners: User or team identifiers.
        labels: Arbitrary key-value labels.
        source_path: Optional file path used during import.
        user_version: Optional caller-friendly version label.

    Returns:
        PromptMetadata: Metadata payload.

    Raises:
        None.

    Examples:
        >>> PromptMetadata(title="Classifier", tags=["support"]).title
        'Classifier'
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    owners: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    source_path: str | None = None
    user_version: str | None = None


class ChatMessage(BaseModel):
    """Concrete chat message template.

    Args:
        role: Message role.
        template: Message template body.
        name: Optional participant name.
        additional_kwargs: Additional message metadata.

    Returns:
        ChatMessage: Chat message template object.

    Raises:
        None.

    Examples:
        >>> ChatMessage(role=MessageRole.HUMAN, template="{question}").template
        '{question}'
    """

    model_config = ConfigDict(extra="forbid")

    role: MessageRole
    template: str
    name: str | None = None
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)


class MessagePlaceholder(BaseModel):
    """Placeholder for a runtime list of messages.

    Args:
        variable_name: Input variable containing a list of messages.
        optional: Whether an empty value is allowed.

    Returns:
        MessagePlaceholder: Placeholder model.

    Raises:
        None.

    Examples:
        >>> MessagePlaceholder(variable_name="history").variable_name
        'history'
    """

    model_config = ConfigDict(extra="forbid")

    variable_name: str
    optional: bool = False


class FewShotBlock(BaseModel):
    """Lightweight few-shot configuration.

    Args:
        examples: Example variable mappings.
        string_template: Template used for string examples.
        chat_messages: Message templates used for chat examples.
        insert_at: Insertion index in chat mode.
        example_separator: Separator used in string mode.

    Returns:
        FewShotBlock: Few-shot configuration.

    Raises:
        ValueError: If neither a string template nor chat messages are supplied.

    Examples:
        >>> FewShotBlock(examples=[{"x": "1"}], string_template="{x}").examples[0]["x"]
        '1'
    """

    model_config = ConfigDict(extra="forbid")

    examples: list[dict[str, Any]]
    string_template: str | None = None
    chat_messages: list[ChatMessage] = Field(default_factory=list)
    insert_at: int = 0
    example_separator: str = "\n\n"

    @model_validator(mode="after")
    def _validate_mode(self) -> FewShotBlock:
        """Validate that the few-shot block can render.

        Args:
            self: Model instance.

        Returns:
            FewShotBlock: Validated instance.

        Raises:
            ValueError: If no rendering template was provided.

        Examples:
            >>> FewShotBlock(examples=[{"x": "1"}], string_template="{x}")
            FewShotBlock(examples=[{'x': '1'}], ...)
        """
        if self.string_template is None and not self.chat_messages:
            raise ValueError("FewShotBlock requires string_template or chat_messages.")
        return self


class PromptSpec(BaseModel):
    """Prompt definition that can render directly or materialize into LangChain.

    Args:
        kind: Prompt kind.
        template_format: Template engine.
        template: Root template for string prompts.
        messages: Message sequence for chat prompts.
        input_variables: Declared required variables.
        optional_variables: Declared optional variables.
        partial_variables: Stored partial variables merged at render time.
        few_shot: Optional few-shot examples.
        metadata: Rich prompt metadata.

    Returns:
        PromptSpec: Prompt definition.

    Raises:
        ValueError: If the shape is invalid for the selected prompt kind.

    Examples:
        >>> PromptSpec(kind=PromptKind.STRING, template="Hello {name}").declared_variables
        ['name']
    """

    model_config = ConfigDict(extra="forbid")

    kind: PromptKind
    template_format: TemplateFormat = TemplateFormat.FSTRING
    template: str | None = None
    messages: list[ChatMessage | MessagePlaceholder] = Field(default_factory=list)
    input_variables: list[str] = Field(default_factory=list)
    optional_variables: list[str] = Field(default_factory=list)
    partial_variables: dict[str, Any] = Field(default_factory=dict)
    few_shot: FewShotBlock | None = None
    metadata: PromptMetadata = Field(default_factory=PromptMetadata)

    @model_validator(mode="before")
    @classmethod
    def _drop_computed_fields(cls, data: Any) -> Any:
        """Drop computed-only fields supplied by serialized payloads.

        Args:
            data: Raw model input.

        Returns:
            Any: Sanitized input.

        Raises:
            None.

        Examples:
            >>> data = {"kind": "string", "template": "Hi", "declared_variables": []}
            >>> PromptSpec.model_validate(data).template
            'Hi'
        """
        if isinstance(data, dict):
            payload = dict(data)
            payload.pop("declared_variables", None)
            return payload
        return data

    @model_validator(mode="after")
    def _validate_shape(self) -> PromptSpec:
        """Validate prompt shape against the selected kind.

        Args:
            self: Model instance.

        Returns:
            PromptSpec: Validated prompt spec.

        Raises:
            ValueError: If the prompt shape is inconsistent.

        Examples:
            >>> msgs = [ChatMessage(role=MessageRole.HUMAN, template="{x}")]
            >>> spec = PromptSpec(kind=PromptKind.CHAT, messages=msgs)
            >>> spec.kind
            <PromptKind.CHAT: 'chat'>
        """
        if self.kind is PromptKind.STRING and not self.template:
            raise ValueError("String prompts require a template.")
        if self.kind is PromptKind.CHAT and not self.messages:
            raise ValueError("Chat prompts require at least one message.")
        if self.kind is PromptKind.STRING and self.messages:
            raise ValueError("String prompts cannot declare chat messages.")
        if self.kind is PromptKind.CHAT and self.template is not None:
            raise ValueError("Chat prompts cannot declare a root template.")
        return self

    @computed_field
    @property
    def declared_variables(self) -> list[str]:
        """Return discovered and explicitly declared variables.

        Args:
            self: Model instance.

        Returns:
            list[str]: Sorted variable names.

        Raises:
            None.

        Examples:
            >>> PromptSpec(kind=PromptKind.STRING, template="{x} {y}").declared_variables
            ['x', 'y']
        """
        variables = set(self.input_variables)
        if self.template:
            variables.update(extract_variables(self.template, self.template_format))
        for entry in self.messages:
            if isinstance(entry, ChatMessage):
                variables.update(extract_variables(entry.template, self.template_format))
            else:
                variables.add(entry.variable_name)
        if self.few_shot and self.few_shot.string_template:
            variables.update(extract_variables(self.few_shot.string_template, self.template_format))
        return sorted(variables)

    def merged_variables(self, variables: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Merge runtime variables with stored partial variables.

        Args:
            variables: Runtime variables.

        Returns:
            dict[str, Any]: Merged variables.

        Raises:
            None.

        Examples:
            >>> spec = PromptSpec(
            ...     kind=PromptKind.STRING, template="{name}",
            ...     partial_variables={"name": "Will"},
            ... )
            >>> spec.merged_variables({})
            {'name': 'Will'}
        """
        merged = dict(self.partial_variables)
        if variables:
            merged.update(dict(variables))
        return merged

    def render_text(self, variables: Mapping[str, Any] | None = None) -> str:
        """Render a string prompt.

        Args:
            variables: Runtime variables.

        Returns:
            str: Rendered text.

        Raises:
            TypeError: If called on a chat prompt.

        Examples:
            >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hello {name}")
            >>> spec.render_text({"name": "Will"})
            'Hello Will'
        """
        if self.kind is not PromptKind.STRING:
            raise TypeError("render_text() is only valid for string prompts.")
        merged = self.merged_variables(variables)
        body = render_template(self.template or "", merged, self.template_format)
        if self.few_shot and self.few_shot.string_template:
            rendered_examples = [
                render_template(self.few_shot.string_template, example, self.template_format)
                for example in self.few_shot.examples
            ]
            return self.few_shot.example_separator.join([*rendered_examples, body])
        return body

    def render_messages(self, variables: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Render a chat prompt.

        Args:
            variables: Runtime variables.

        Returns:
            list[dict[str, Any]]: Rendered message payloads.

        Raises:
            TypeError: If called on a string prompt.
            KeyError: If a required placeholder variable is missing.

        Examples:
            >>> msgs = [ChatMessage(role=MessageRole.HUMAN, template="Hi {name}")]
            >>> spec = PromptSpec(kind=PromptKind.CHAT, messages=msgs)
            >>> spec.render_messages({"name": "Will"})[0]["content"]
            'Hi Will'
        """
        if self.kind is not PromptKind.CHAT:
            raise TypeError("render_messages() is only valid for chat prompts.")
        merged = self.merged_variables(variables)
        messages: list[dict[str, Any]] = []
        for entry in self.messages:
            if isinstance(entry, ChatMessage):
                messages.append(
                    {
                        "role": entry.role.value,
                        "content": render_template(entry.template, merged, self.template_format),
                        "name": entry.name,
                        "additional_kwargs": entry.additional_kwargs,
                    }
                )
            else:
                value = merged.get(entry.variable_name)
                if value is None:
                    if entry.optional:
                        continue
                    raise KeyError(f"Missing message placeholder variable: {entry.variable_name}")
                if not isinstance(value, list):
                    raise TypeError(
                        f"Placeholder '{entry.variable_name}' must be a list of messages."
                    )
                messages.extend(value)
        if self.few_shot and self.few_shot.chat_messages:
            rendered_examples: list[dict[str, Any]] = []
            for example in self.few_shot.examples:
                for message in self.few_shot.chat_messages:
                    rendered_examples.append(
                        {
                            "role": message.role.value,
                            "content": render_template(
                                message.template,
                                example,
                                self.template_format,
                            ),
                            "name": message.name,
                            "additional_kwargs": message.additional_kwargs,
                        }
                    )
            index = max(0, min(self.few_shot.insert_at, len(messages)))
            messages = messages[:index] + rendered_examples + messages[index:]
        return messages

    def to_langchain(self) -> Any:
        """Materialize the prompt into a LangChain prompt object.

        Args:
            self: Model instance.

        Returns:
            Any: LangChain prompt object.

        Raises:
            ImportError: If ``langchain-core`` is unavailable.

        Examples:
            >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> spec.to_langchain().__class__.__name__
            'PromptTemplate'
        """
        try:
            from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
            from langchain_core.prompts.chat import MessagesPlaceholder as LcMessagesPlaceholder
        except ImportError as exc:
            raise ImportError("langchain-core is required for materialization.") from exc
        if self.kind is PromptKind.STRING:
            return PromptTemplate(
                template=self.template or "",
                input_variables=self.input_variables or self.declared_variables,
                partial_variables=self.partial_variables,
                template_format=self.template_format.value,
            )
        normalized_messages: list[Any] = []
        for entry in self.messages:
            if isinstance(entry, ChatMessage):
                if entry.role is not MessageRole.GENERIC:
                    role = entry.role.value
                else:
                    role = entry.name or "generic"
                normalized_messages.append((role, entry.template))
            else:
                normalized_messages.append(
                    LcMessagesPlaceholder(
                        variable_name=entry.variable_name,
                        optional=entry.optional,
                    )
                )
        return ChatPromptTemplate(
            messages=normalized_messages,
            partial_variables=self.partial_variables,
            template_format=self.template_format.value,
        )


def render_template(template: str, variables: Mapping[str, Any], fmt: TemplateFormat) -> str:
    """Render a template with the selected engine.

    Args:
        template: Template text.
        variables: Runtime variables.
        fmt: Template format.

    Returns:
        str: Rendered text.

    Raises:
        KeyError: If a required variable is missing.

    Examples:
        >>> render_template("Hello {name}", {"name": "Will"}, TemplateFormat.FSTRING)
        'Hello Will'
    """
    if fmt is TemplateFormat.FSTRING:
        return template.format_map(dict(variables))
    if fmt is TemplateFormat.JINJA2:
        environment = Environment(undefined=StrictUndefined, autoescape=False)
        return environment.from_string(template).render(**dict(variables))
    if fmt is TemplateFormat.MUSTACHE:
        return re.sub(
            r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}",
            lambda match: str(variables.get(match.group(1), "")),
            template,
        )
    raise ValueError(f"Unsupported template format: {fmt}")


def extract_variables(template: str, fmt: TemplateFormat) -> list[str]:
    """Extract variable names from a template.

    Args:
        template: Template text.
        fmt: Template format.

    Returns:
        list[str]: Sorted variable names.

    Raises:
        None.

    Examples:
        >>> extract_variables("Hello {name}", TemplateFormat.FSTRING)
        ['name']
    """
    if fmt is TemplateFormat.FSTRING:
        return sorted({field for _, field, _, _ in Formatter().parse(template) if field})
    return sorted(set(re.findall(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}", template)))


class PromptRef(BaseModel):
    """Reference to a prompt and selector.

    Args:
        namespace: Prompt namespace.
        name: Prompt name.
        selector: Alias, user-facing version label, or concrete version id.

    Returns:
        PromptRef: Reference payload.

    Raises:
        None.

    Examples:
        >>> PromptRef.parse("support/triage:production").selector
        'production'
    """

    model_config = ConfigDict(extra="forbid")

    namespace: str
    name: str
    selector: str = "latest"

    @model_validator(mode="before")
    @classmethod
    def _drop_ref_computed_fields(cls, data: Any) -> Any:
        """Drop computed-only fields from serialized prompt references.

        Args:
            data: Raw model input.

        Returns:
            Any: Sanitized input.

        Raises:
            None.

        Examples:
            >>> data = {"namespace": "x", "name": "y", "selector": "latest", "resource_id": "x/y"}
            >>> PromptRef.model_validate(data).selector
            'latest'
        """
        if isinstance(data, dict):
            payload = dict(data)
            payload.pop("resource_id", None)
            payload.pop("full_name", None)
            return payload
        return data

    @classmethod
    def parse(cls, value: str) -> PromptRef:
        """Parse a compact ``namespace/name:selector`` reference.

        Args:
            value: Compact reference string.

        Returns:
            PromptRef: Parsed prompt reference.

        Raises:
            ValueError: If the input is malformed.

        Examples:
            >>> PromptRef.parse("support/triage")
            PromptRef(namespace='support', name='triage', selector='latest')
        """
        selector = "latest"
        body = value.strip()
        if not body:
            raise ValueError("Prompt reference cannot be empty.")
        if ":" in body:
            body, selector = body.rsplit(":", 1)
        if "/" not in body:
            raise ValueError("Prompt reference must look like 'namespace/name[:selector]'.")
        namespace, name = body.split("/", 1)
        if not namespace or not name:
            raise ValueError("Prompt reference must include namespace and name.")
        return cls(namespace=namespace, name=name, selector=selector or "latest")

    @computed_field
    @property
    def resource_id(self) -> str:
        """Return the stable prompt resource identifier.

        Args:
            self: Model instance.

        Returns:
            str: ``namespace/name`` identifier.

        Raises:
            None.

        Examples:
            >>> PromptRef(namespace="support", name="triage").resource_id
            'support/triage'
        """
        return f"{self.namespace}/{self.name}"

    @computed_field
    @property
    def full_name(self) -> str:
        """Return the fully-qualified prompt reference.

        Args:
            self: Model instance.

        Returns:
            str: ``namespace/name:selector`` identifier.

        Raises:
            None.

        Examples:
            >>> PromptRef(namespace="support", name="triage", selector="production").full_name
            'support/triage:production'
        """
        return f"{self.resource_id}:{self.selector}"


class PromptRegistration(BaseModel):
    """Registration request payload.

    Args:
        namespace: Prompt namespace.
        name: Prompt name.
        spec: Prompt spec.
        created_by: Creator identifier.
        alias: Alias to move after registration.

    Returns:
        PromptRegistration: Registration payload.

    Raises:
        None.

    Examples:
        >>> spec = PromptSpec(kind=PromptKind.STRING, template="hi")
        >>> PromptRegistration(namespace="x", name="y", spec=spec).name
        'y'
    """

    model_config = ConfigDict(extra="forbid")

    namespace: str
    name: str
    spec: PromptSpec
    created_by: str | None = None
    alias: str | None = "latest"


class AliasMove(BaseModel):
    """Alias movement payload.

    Args:
        alias: Alias name.
        version_id: Target version id.

    Returns:
        AliasMove: Alias movement request.

    Raises:
        None.

    Examples:
        >>> AliasMove(alias="production", version_id="v1").alias
        'production'
    """

    model_config = ConfigDict(extra="forbid")

    alias: str
    version_id: str


class PromptAssetView(BaseModel):
    """Blob-backed asset metadata linked to a prompt version.

    Args:
        asset_id: Unique asset id.
        version_id: Owning prompt version id.
        kind: Asset kind.
        storage_backend: Storage backend name.
        bucket: Logical or physical bucket/container name.
        object_key: Blob object key.
        content_type: MIME content type.
        byte_size: Optional object size.
        checksum_sha256: Optional checksum.
        metadata_json: User-defined metadata.
        created_at: Creation timestamp.

    Returns:
        PromptAssetView: Asset metadata.

    Raises:
        None.

    Examples:
        >>> av = PromptAssetView(
        ...     asset_id='a', version_id='v',
        ...     kind=PromptAssetKind.EXPORT_BUNDLE,
        ...     storage_backend='local', bucket='promptdb',
        ...     object_key='x.json',
        ... )
        >>> av.object_key
        'x.json'
    """

    model_config = ConfigDict(extra="forbid")

    asset_id: str
    version_id: str
    kind: PromptAssetKind
    storage_backend: str
    bucket: str
    object_key: str
    content_type: str | None = None
    byte_size: int | None = None
    checksum_sha256: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class PromptVersionView(BaseModel):
    """API-ready view over an immutable prompt version.

    Args:
        version_id: Version identifier.
        namespace: Prompt namespace.
        name: Prompt name.
        revision: Monotonic revision.
        user_version: User-facing version label.
        spec: Prompt spec.
        created_by: Creator identifier.
        aliases: Aliases pointing to this version.

    Returns:
        PromptVersionView: Prompt version view.

    Raises:
        None.

    Examples:
        >>> spec = PromptSpec(kind=PromptKind.STRING, template="hi")
        >>> view = PromptVersionView(
        ...     version_id="v1", namespace="x", name="y",
        ...     revision=1, spec=spec,
        ... )
        >>> view.revision
        1
    """

    model_config = ConfigDict(extra="forbid")

    version_id: str
    namespace: str
    name: str
    revision: int
    user_version: str | None = None
    spec: PromptSpec
    created_by: str | None = None
    created_at: Any | None = None
    aliases: list[str] = Field(default_factory=list)
    assets: list[PromptAssetView] = Field(default_factory=list)

    @computed_field
    @property
    def ref(self) -> PromptRef:
        """Return a convenient immutable reference to this exact version.

        Args:
            self: Model instance.

        Returns:
            PromptRef: Version reference.

        Raises:
            None.

        Examples:
            >>> spec = PromptSpec(kind=PromptKind.STRING, template="hi")
            >>> view = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y",
            ...     revision=1, spec=spec,
            ... )
            >>> view.ref.full_name
            'x/y:v1'
        """
        return PromptRef(namespace=self.namespace, name=self.name, selector=self.version_id)

    def render(self, variables: Mapping[str, Any] | None = None) -> PromptRenderResult:
        """Render the current version directly.

        Args:
            variables: Runtime variables.

        Returns:
            PromptRenderResult: Render output.

        Raises:
            TypeError: If the prompt kind is unsupported.

        Examples:
            >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> view = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y",
            ...     revision=1, spec=spec,
            ... )
            >>> view.render({"name": "Will"}).text
            'Hi Will'
        """
        ref = PromptRef(namespace=self.namespace, name=self.name, selector=self.version_id)
        if self.spec.kind is PromptKind.STRING:
            return PromptRenderResult(
                ref=ref,
                version=self,
                text=self.spec.render_text(variables),
            )
        return PromptRenderResult(
            ref=ref,
            version=self,
            messages=self.spec.render_messages(variables),
        )

    def as_langchain(self) -> Any:
        """Materialize the current version into a LangChain prompt.

        Args:
            self: Model instance.

        Returns:
            Any: LangChain prompt object.

        Raises:
            ImportError: If ``langchain-core`` is unavailable.

        Examples:
            >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> view = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y",
            ...     revision=1, spec=spec,
            ... )
            >>> view.as_langchain().__class__.__name__
            'PromptTemplate'
        """
        return self.spec.to_langchain()

    def wrap(self) -> ResolvedPrompt:
        """Wrap the version in an ergonomic resolved-prompt object.

        Args:
            self: Model instance.

        Returns:
            ResolvedPrompt: Wrapper exposing render and materialization helpers.

        Raises:
            None.

        Examples:
            >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> view = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y",
            ...     revision=1, spec=spec,
            ... )
            >>> view.wrap().ref.full_name
            'x/y:v1'
        """
        return ResolvedPrompt(version=self)


class ResolvedPrompt(BaseModel):
    """Ergonomic wrapper around a resolved prompt version.

    Args:
        version: Resolved prompt version.

    Returns:
        ResolvedPrompt: Rich wrapper object.

    Raises:
        None.

    Examples:
        >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
        >>> version = PromptVersionView(
        ...     version_id="v1", namespace="x", name="y",
        ...     revision=1, spec=spec,
        ... )
        >>> ResolvedPrompt(version=version).ref.full_name
        'x/y:v1'
    """

    model_config = ConfigDict(extra="forbid")

    version: PromptVersionView

    @computed_field
    @property
    def ref(self) -> PromptRef:
        """Return an immutable reference to the concrete version.

        Args:
            self: Model instance.

        Returns:
            PromptRef: Version reference.

        Raises:
            None.

        Examples:
            >>> _s = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> version = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
            ... )
            >>> ResolvedPrompt(version=version).ref.selector
            'v1'
        """
        return PromptRef(
            namespace=self.version.namespace,
            name=self.version.name,
            selector=self.version.version_id,
        )

    def as_langchain(self) -> Any:
        """Materialize the wrapped prompt as a LangChain object.

        Args:
            self: Model instance.

        Returns:
            Any: LangChain prompt object.

        Raises:
            ImportError: If ``langchain-core`` is unavailable.

        Examples:
            >>> _s = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> version = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
            ... )
            >>> ResolvedPrompt(version=version).as_langchain().__class__.__name__
            'PromptTemplate'
        """
        return self.version.as_langchain()

    def render(self, variables: Mapping[str, Any] | None = None) -> PromptRenderResult:
        """Render the wrapped prompt.

        Args:
            variables: Runtime variables.

        Returns:
            PromptRenderResult: Rendered prompt output.

        Raises:
            TypeError: If the prompt kind and helper mismatch.

        Examples:
            >>> _s = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> version = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
            ... )
            >>> ResolvedPrompt(version=version).render({"name": "Will"}).text
            'Hi Will'
        """
        return self.version.render(variables)

    def render_text(self, variables: Mapping[str, Any] | None = None) -> str:
        """Render the wrapped prompt as text.

        Args:
            variables: Runtime variables.

        Returns:
            str: Rendered text.

        Raises:
            TypeError: If the wrapped prompt is not a string prompt.

        Examples:
            >>> _s = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> version = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
            ... )
            >>> ResolvedPrompt(version=version).render_text({"name": "Will"})
            'Hi Will'
        """
        result = self.render(variables)
        if result.text is None:
            raise TypeError("Resolved prompt does not render to text.")
        return result.text

    def render_messages(self, variables: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Render the wrapped prompt as messages.

        Args:
            variables: Runtime variables.

        Returns:
            list[dict[str, Any]]: Rendered chat messages.

        Raises:
            TypeError: If the wrapped prompt is not a chat prompt.

        Examples:
            >>> _msg = ChatMessage(role=MessageRole.HUMAN, template="{question}")
            >>> _s = PromptSpec(kind=PromptKind.CHAT, messages=[_msg])
            >>> version = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
            ... )
            >>> ResolvedPrompt(version=version).render_messages({"question": "Hi"})[0]["content"]
            'Hi'
        """
        result = self.render(variables)
        if not result.messages:
            raise TypeError("Resolved prompt does not render to messages.")
        return result.messages

    def invoke(self, variables: Mapping[str, Any] | None = None) -> Any:
        """Invoke the underlying LangChain prompt object.

        Args:
            variables: Runtime variables.

        Returns:
            Any: LangChain prompt value.

        Raises:
            AttributeError: If the underlying object lacks ``invoke``.

        Examples:
            >>> _s = PromptSpec(kind=PromptKind.STRING, template="Hi {name}")
            >>> version = PromptVersionView(
            ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
            ... )
            >>> ResolvedPrompt(version=version).invoke({"name": "Will"}).text
            'Hi Will'
        """
        prompt = self.as_langchain()
        return prompt.invoke(dict(variables or {}))


class PromptRenderResult(BaseModel):
    """Rendered prompt result.

    Args:
        ref: Prompt reference.
        version: Resolved version.
        text: Rendered string prompt.
        messages: Rendered chat messages.

    Returns:
        PromptRenderResult: Render result.

    Raises:
        None.

    Examples:
        >>> _s = PromptSpec(kind=PromptKind.STRING, template="hi")
        >>> view = PromptVersionView(
        ...     version_id="v1", namespace="x", name="y", revision=1, spec=_s,
        ... )
        >>> ref = PromptRef(namespace="x", name="y")
        >>> PromptRenderResult(ref=ref, version=view, text="hi").text
        'hi'
    """

    model_config = ConfigDict(extra="forbid")

    ref: PromptRef
    version: PromptVersionView
    text: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
