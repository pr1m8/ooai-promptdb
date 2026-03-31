"""Integration tests for the service and repository layers."""

from pathlib import Path

import pytest

from promptdb.db import create_all, create_session_factory
from promptdb.domain import (
    ChatMessage,
    MessageRole,
    PromptKind,
    PromptMetadata,
    PromptRef,
    PromptRegistration,
    PromptSpec,
)
from promptdb.service import PromptService
from promptdb.storage import LocalBlobStore


@pytest.mark.integration
def test_register_resolve_render_and_export(tmp_path: Path) -> None:
    """Exercise the core service flow against SQLite and local storage."""
    database_path = tmp_path / 'promptdb.sqlite3'
    session_factory = create_session_factory(f'sqlite:///{database_path}')
    create_all(f'sqlite:///{database_path}')
    blob_store = LocalBlobStore(tmp_path / 'blobs')
    service = PromptService(session_factory, blob_store)

    spec = PromptSpec(
        kind=PromptKind.CHAT,
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, template='You are {persona}.'),
            ChatMessage(role=MessageRole.HUMAN, template='{question}'),
        ],
        metadata=PromptMetadata(
            title='Support triage',
            description='Primary support triage prompt',
            tags=['support', 'triage'],
            user_version='2026.03.31.1',
        ),
        partial_variables={'persona': 'a senior support analyst'},
    )

    version = service.register(
        PromptRegistration(
            namespace='support',
            name='triage',
            spec=spec,
            created_by='will',
            alias='production',
        )
    )
    assert version.revision == 1
    assert 'production' in version.aliases

    resolved = service.resolve(PromptRef(namespace='support', name='triage', selector='production'))
    assert resolved.version_id == version.version_id

    rendered = service.render(
        PromptRef(namespace='support', name='triage', selector='production'),
        {'question': 'Where is my refund?'},
    )
    assert rendered.messages[0]['content'] == 'You are a senior support analyst.'
    assert rendered.messages[1]['content'] == 'Where is my refund?'

    export_key = service.export_bundle(resolved)
    exported = blob_store.get_text(export_key)
    assert '"namespace": "support"' in exported
    assert '"name": "triage"' in exported


@pytest.mark.integration
def test_client_registers_structured_yaml_and_resolves_user_version(tmp_path: Path) -> None:
    """Register a structured YAML prompt file and resolve it by user version."""
    from promptdb.client import PromptClient
    from promptdb.files import save_prompt_spec
    from promptdb.settings import AppSettings

    prompt_path = tmp_path / 'prompts' / 'triage.yaml'
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    spec = PromptSpec(
        kind=PromptKind.STRING,
        template='Hello {{ name }}',
        template_format='jinja2',
        metadata=PromptMetadata(
            title='Greeting',
            description='Structured YAML example',
            tags=['example', 'jinja2'],
            user_version='2026.04.01.1',
        ),
    )
    save_prompt_spec(spec, prompt_path)

    settings = AppSettings(
        database_url=f'sqlite:///{tmp_path / "promptdb.sqlite3"}',
        blob_root=str(tmp_path / 'blobs'),
    )
    client = PromptClient.from_env(settings)
    version = client.register_file(
        path=prompt_path,
        namespace='examples',
        name='greeting',
        alias='production',
    )

    assert version.user_version == '2026.04.01.1'
    resolved = client.resolve('examples/greeting:2026.04.01.1')
    assert resolved.version_id == version.version_id
    greeting = client.get('examples/greeting:production')
    assert greeting.render_text({'name': 'Will'}) == 'Hello Will'


@pytest.mark.integration
def test_duplicate_user_version_is_rejected(tmp_path: Path) -> None:
    """Reject duplicate user-facing versions for the same prompt."""
    database_path = tmp_path / 'promptdb.sqlite3'
    session_factory = create_session_factory(f'sqlite:///{database_path}')
    create_all(f'sqlite:///{database_path}')
    service = PromptService(session_factory, LocalBlobStore(tmp_path / 'blobs'))

    first_spec = PromptSpec(
        kind=PromptKind.STRING,
        template='v1: {question}',
        metadata=PromptMetadata(user_version='2026.04.01.1'),
    )
    second_spec = PromptSpec(
        kind=PromptKind.STRING,
        template='v2: {question}',
        metadata=PromptMetadata(user_version='2026.04.01.1'),
    )
    service.register(
        PromptRegistration(
            namespace='support',
            name='classifier',
            spec=first_spec,
        )
    )

    with pytest.raises(ValueError):
        service.register(
            PromptRegistration(
                namespace='support',
                name='classifier',
                spec=second_spec,
            )
        )


@pytest.mark.integration
def test_revision_selector_resolves_exact_revision(tmp_path: Path) -> None:
    """Resolve a version by explicit revision selector."""
    database_path = tmp_path / 'promptdb.sqlite3'
    session_factory = create_session_factory(f'sqlite:///{database_path}')
    create_all(f'sqlite:///{database_path}')
    service = PromptService(session_factory, LocalBlobStore(tmp_path / 'blobs'))

    service.register(
        PromptRegistration(
            namespace='support',
            name='classifier',
            spec=PromptSpec(
                kind=PromptKind.STRING, template='v1',
            ),
        )
    )
    second = service.register(
        PromptRegistration(
            namespace='support',
            name='classifier',
            spec=PromptSpec(
                kind=PromptKind.STRING, template='v2',
            ),
        )
    )

    resolved = service.resolve(PromptRef(namespace='support', name='classifier', selector='rev:2'))
    assert resolved.version_id == second.version_id
    assert resolved.spec.template == 'v2'


def test_export_bundle_creates_asset_row(service, prompt_registration):
    """Verify that exporting a bundle creates an asset metadata row."""
    version = service.register(prompt_registration)
    asset = service.export_bundle(version)
    assert asset.object_key.endswith('.json')
    assets = service.list_assets(version.ref)
    assert len(assets) >= 1
    assert assets[0].kind.value == 'export_bundle'
