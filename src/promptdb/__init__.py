"""Prompt registry and runtime delivery layer for LangChain and LangGraph.

``promptdb`` lets you version, alias, and deliver prompts through a relational
database, export them to blob storage, and access them from Python, a FastAPI
API, a Rich CLI, or a Streamlit dashboard.

Typical usage::

    from promptdb import PromptClient, PromptKind, PromptMetadata

    client = PromptClient.from_env()

    # Register a prompt
    client.register_text(
        namespace="support",
        name="triage",
        template="You are a {persona}. Question: {question}",
        kind=PromptKind.STRING,
        alias="production",
        metadata=PromptMetadata(title="Triage", user_version="v1"),
        partial_variables={"persona": "senior analyst"},
    )

    # Resolve and render
    resolved = client.get("support/triage:production")
    print(resolved.render_text({"question": "Where is my refund?"}))

    # Materialize as a LangChain prompt
    lc_prompt = resolved.as_langchain()

Key components:

- :class:`PromptClient` — ergonomic facade for all prompt operations
- :class:`PromptSpec` — typed prompt definition (string or chat, with
  template format, partials, few-shot, and metadata)
- :class:`PromptRef` — compact ``namespace/name:selector`` reference
- :class:`PromptVersionView` — immutable view of a stored version
- :class:`ResolvedPrompt` — wrapper with render and LangChain helpers
- :class:`PromptService` — orchestration layer shared by API and CLI
- :class:`AppSettings` — ``PROMPTDB_*`` environment variable config
"""

from promptdb.client import PromptClient
from promptdb.domain import (
    AliasMove,
    ChatMessage,
    FewShotBlock,
    MessagePlaceholder,
    MessageRole,
    PromptAssetKind,
    PromptAssetView,
    PromptKind,
    PromptMetadata,
    PromptRef,
    PromptRegistration,
    PromptRenderResult,
    PromptSpec,
    PromptVersionView,
    ResolvedPrompt,
    TemplateFormat,
)
from promptdb.service import PromptService
from promptdb.settings import AppSettings

__all__ = [
    "AliasMove",
    "AppSettings",
    "ChatMessage",
    "FewShotBlock",
    "MessagePlaceholder",
    "MessageRole",
    "PromptAssetKind",
    "PromptAssetView",
    "PromptClient",
    "PromptKind",
    "PromptMetadata",
    "PromptRef",
    "PromptRegistration",
    "PromptRenderResult",
    "PromptService",
    "PromptSpec",
    "PromptVersionView",
    "ResolvedPrompt",
    "TemplateFormat",
]
