"""Unit tests for file workflows and the ergonomic client wrapper."""

from pathlib import Path

from promptdb.client import PromptClient
from promptdb.domain import PromptKind, PromptMetadata, PromptRef, PromptSpec
from promptdb.files import load_prompt_file, save_prompt_spec
from promptdb.settings import AppSettings


def test_prompt_ref_parse_and_full_name() -> None:
    """Parse compact prompt refs into explicit fields."""
    ref = PromptRef.parse("support/triage:production")
    assert ref.namespace == "support"
    assert ref.name == "triage"
    assert ref.selector == "production"
    assert ref.full_name == "support/triage:production"


def test_save_and_load_prompt_spec_yaml(tmp_path: Path) -> None:
    """Round-trip a structured prompt spec through YAML."""
    spec = PromptSpec(
        kind=PromptKind.STRING,
        template="Hello {{ name }}",
        metadata=PromptMetadata(title="Greeting", user_version="2026.03.31.3"),
    )
    output = tmp_path / "greeting.yaml"
    save_prompt_spec(spec, output)

    loaded = load_prompt_file(output)
    assert loaded.kind is PromptKind.STRING
    assert loaded.template == "Hello {{ name }}"
    assert loaded.metadata.title == "Greeting"
    assert loaded.metadata.user_version == "2026.03.31.3"


def test_prompt_client_get_returns_wrapped_prompt(tmp_path: Path) -> None:
    """Return a resolved prompt wrapper with convenience methods."""
    settings = AppSettings(
        database_url=f"sqlite:///{tmp_path / 'promptdb.sqlite3'}",
        blob_root=str(tmp_path / 'blobs'),
    )
    client = PromptClient.from_env(settings)
    client.register_text(namespace="support", name="triage", template="Hello {name}")

    resolved = client.get("support/triage:latest")
    assert resolved.ref.resource_id == "support/triage"
    assert resolved.render_text({"name": "Will"}) == "Hello Will"
