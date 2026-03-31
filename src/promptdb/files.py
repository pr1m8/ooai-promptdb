"""File helpers for :mod:`promptdb`.

Purpose:
    Load prompts from plain-text or structured files and write prompt specs or
    resolved versions back to disk.

Design:
    Plain-text files are convenient for authoring simple prompts, while JSON and
    YAML files can capture the full :class:`~promptdb.domain.PromptSpec` shape.

Attributes:
    load_prompt_file: Create a prompt spec from a file.
    save_prompt_spec: Write a prompt specification to a file.
    write_version_bundle: Write a version view to a file.

Examples:
    .. code-block:: python

        spec = load_prompt_file('prompts/demo.yaml')
        save_prompt_spec(spec, 'build/demo.json')
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from promptdb.domain import (
    ChatMessage,
    MessageRole,
    PromptKind,
    PromptMetadata,
    PromptSpec,
    PromptVersionView,
)

_STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}
_TEXT_SUFFIXES = {".txt", ".md", ".prompt", ".jinja", ".mustache"}


def _normalize_structured_payload(payload: dict[str, Any], source_path: Path) -> PromptSpec:
    """Normalize a structured prompt payload into a prompt spec.

    Args:
        payload: Parsed mapping payload.
        source_path: Source file path.

    Returns:
        PromptSpec: Validated prompt specification.

    Raises:
        ValueError: If the payload shape is invalid.

    Examples:
        >>> spec = _normalize_structured_payload({'kind': 'string', 'template': 'Hi {name}'}, Path('x.yaml'))
        >>> spec.kind.value
        'string'
    """
    data = dict(payload)
    metadata_payload = dict(data.get("metadata") or {})
    metadata_payload.setdefault("source_path", str(source_path))
    data["metadata"] = PromptMetadata.model_validate(metadata_payload)
    return PromptSpec.model_validate(data)


def load_prompt_file(
    path: str | Path,
    *,
    kind: PromptKind | None = None,
    message_role: MessageRole = MessageRole.HUMAN,
) -> PromptSpec:
    """Load a prompt spec from a plain-text or structured file.

    Args:
        path: File path.
        kind: Prompt kind for plain-text files. Structured files can omit this.
        message_role: Message role for plain-text chat prompts.

    Returns:
        PromptSpec: Loaded prompt specification.

    Raises:
        FileNotFoundError: If the file is missing.
        ValueError: If ``kind`` is omitted for plain-text files.

    Examples:
        .. code-block:: python

            spec = load_prompt_file('prompts/demo.txt', kind=PromptKind.STRING)
            spec = load_prompt_file('prompts/demo.yaml')
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in _STRUCTURED_SUFFIXES:
        text = file_path.read_text(encoding="utf-8")
        payload = json.loads(text) if suffix == ".json" else yaml.safe_load(text)
        if not isinstance(payload, dict):
            raise ValueError("Structured prompt files must contain a mapping payload.")
        return _normalize_structured_payload(payload, file_path)

    if kind is None:
        raise ValueError("Plain-text prompt files require an explicit kind.")
    body = file_path.read_text(encoding="utf-8")
    metadata = PromptMetadata(title=file_path.stem, source_path=str(file_path))
    if kind is PromptKind.STRING:
        return PromptSpec(kind=kind, template=body, metadata=metadata)
    return PromptSpec(kind=kind, messages=[ChatMessage(role=message_role, template=body)], metadata=metadata)


def save_prompt_spec(spec: PromptSpec, path: str | Path) -> Path:
    """Write a prompt spec to JSON or YAML.

    Args:
        spec: Prompt specification.
        path: Output file path.

    Returns:
        Path: Output path.

    Raises:
        ValueError: If the suffix is unsupported.
        OSError: If writing fails.

    Examples:
        .. code-block:: python

            save_prompt_spec(spec, 'build/demo.yaml')
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = spec.model_dump(mode="json", exclude_none=True, exclude_computed_fields=True)
    suffix = output_path.suffix.lower()
    if suffix == ".json":
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path
    if suffix in {".yaml", ".yml"}:
        output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return output_path
    raise ValueError("Prompt specs can only be saved as .json, .yaml, or .yml.")


def write_version_bundle(version: PromptVersionView, path: str | Path) -> Path:
    """Write a version bundle to a file.

    Args:
        version: Prompt version.
        path: Output file path.

    Returns:
        Path: Output path.

    Raises:
        OSError: If writing fails.

    Examples:
        .. code-block:: python

            write_version_bundle(version, 'build/version.json')
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = version.model_dump(mode="json", exclude_none=True)
    suffix = output_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    else:
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
