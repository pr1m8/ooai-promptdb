"""Package overview for :mod:`promptdb`.

Purpose:
    Provide a prompt registry and runtime delivery layer for LangChain and
    LangGraph applications.

Design:
    The package centers on :class:`~promptdb.domain.PromptSpec`, which supports
    string prompts, chat prompts, placeholders, lightweight few-shot examples,
    metadata, user-facing version labels, LangChain materialization, and a
    Rich-powered local CLI.

Attributes:
    __all__: Curated public API.

Examples:
    >>> from promptdb import PromptKind, PromptSpec
    >>> spec = PromptSpec(kind=PromptKind.STRING, template="Hello {name}")
    >>> spec.render_text({"name": "Will"})
    'Hello Will'
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
