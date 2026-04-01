"""End-to-end tests that cross the HTTP boundary."""

import pytest

from promptdb.domain import ChatMessage, MessageRole, PromptKind, PromptMetadata, PromptSpec


@pytest.mark.e2e
def test_full_api_registration_resolution_render_and_export(client) -> None:
    """Register a prompt, resolve it, render it, and export it through the API."""
    spec = PromptSpec(
        kind=PromptKind.CHAT,
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, template="You are {persona}."),
            ChatMessage(role=MessageRole.HUMAN, template="{question}"),
        ],
        metadata=PromptMetadata(
            title="Research answerer",
            description="Answers research questions with citations.",
            tags=["research", "answering"],
            owners=["platform"],
            user_version="2026.03.31.2",
        ),
        partial_variables={"persona": "a meticulous research assistant"},
    )

    register_response = client.post(
        "/api/v1/prompts/register",
        json={
            "namespace": "research",
            "name": "answerer",
            "created_by": "will",
            "alias": "production",
            "spec": spec.model_dump(mode="json"),
        },
    )
    assert register_response.status_code == 200, register_response.text
    version = register_response.json()
    assert version["namespace"] == "research"
    assert "production" in version["aliases"]

    resolve_response = client.get(
        "/api/v1/prompts/research/answerer/resolve",
        params={"selector": "production"},
    )
    assert resolve_response.status_code == 200, resolve_response.text
    resolved = resolve_response.json()
    assert resolved["version_id"] == version["version_id"]

    render_response = client.post(
        "/api/v1/prompts/research/answerer/render",
        params={"selector": "production"},
        json={"variables": {"question": "How does CAP compare to PACELC?"}},
    )
    assert render_response.status_code == 200, render_response.text
    rendered = render_response.json()
    assert rendered["messages"][0]["content"] == "You are a meticulous research assistant."
    assert rendered["messages"][1]["content"] == "How does CAP compare to PACELC?"

    export_response = client.get("/api/v1/exports/research/answerer/production")
    assert export_response.status_code == 200, export_response.text
    assert export_response.json()["object_key"].startswith("exports/research/answerer/")


@pytest.mark.e2e
def test_alias_promotion_between_versions(client) -> None:
    """Create two versions and move production to the newer one."""
    first_spec = PromptSpec(
        kind=PromptKind.STRING,
        template="v1: {question}",
        metadata=PromptMetadata(user_version="1.0.0"),
    )
    second_spec = PromptSpec(
        kind=PromptKind.STRING,
        template="v2: {question}",
        metadata=PromptMetadata(user_version="1.1.0"),
    )

    first = client.post(
        "/api/v1/prompts/register",
        json={
            "namespace": "support",
            "name": "classifier",
            "spec": first_spec.model_dump(mode="json"),
            "alias": "production",
        },
    ).json()
    second = client.post(
        "/api/v1/prompts/register",
        json={
            "namespace": "support",
            "name": "classifier",
            "spec": second_spec.model_dump(mode="json"),
            "alias": "candidate",
        },
    ).json()

    move = client.post(
        "/api/v1/prompts/support/classifier/aliases/production",
        json={"alias": "production", "version_id": second["version_id"]},
    )
    assert move.status_code == 200, move.text

    render = client.post(
        "/api/v1/prompts/support/classifier/render",
        params={"selector": "production"},
        json={"variables": {"question": "hello"}},
    )
    assert render.status_code == 200, render.text
    assert render.json()["text"] == "v2: hello"
    assert first["version_id"] != second["version_id"]
