"""Shared pytest fixtures for :mod:`promptdb`.

Purpose:
    Provide isolated settings and API client fixtures for unit, integration, and
    end-to-end tests.

Design:
    Tests use SQLite plus local filesystem blobs to avoid external services.

Attributes:
    app_settings: Per-test settings fixture.
    client: FastAPI test client.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from promptdb.api import create_app
from promptdb.settings import AppSettings


@pytest.fixture()
def app_settings(tmp_path: Path) -> AppSettings:
    """Build per-test application settings.

    Args:
        tmp_path: Temporary path fixture.

    Returns:
        AppSettings: Test settings.

    Raises:
        None.

    Examples:
        None.
    """
    database_path = tmp_path / "promptdb.sqlite3"
    blob_root = tmp_path / "blobs"
    return AppSettings(
        database_url=f"sqlite:///{database_path}",
        blob_root=str(blob_root),
        storage_backend="local",
        api_prefix="/api/v1",
    )


@pytest.fixture()
def client(app_settings: AppSettings) -> TestClient:
    """Create a test client for the API.

    Args:
        app_settings: Test settings.

    Returns:
        TestClient: FastAPI test client.

    Raises:
        None.

    Examples:
        None.
    """
    app = create_app(app_settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def service(tmp_path: Path):
    """Create a prompt service backed by SQLite and local blob storage.

    Args:
        tmp_path: Temporary path fixture.

    Returns:
        PromptService: Configured service instance.

    Raises:
        None.
    """
    from promptdb.db import create_all, create_session_factory
    from promptdb.service import PromptService
    from promptdb.storage import LocalBlobStore

    database_url = f"sqlite:///{tmp_path / 'promptdb.sqlite3'}"
    create_all(database_url)
    return PromptService(create_session_factory(database_url), LocalBlobStore(tmp_path / "blobs"))


@pytest.fixture()
def prompt_registration():
    """Create a representative prompt registration payload.

    Args:
        None.

    Returns:
        PromptRegistration: Sample registration payload.

    Raises:
        None.
    """
    from promptdb.domain import PromptKind, PromptMetadata, PromptRegistration, PromptSpec

    return PromptRegistration(
        namespace="support",
        name="triage",
        spec=PromptSpec(
            kind=PromptKind.STRING,
            template="Hello {name}",
            metadata=PromptMetadata(user_version="fixture.1"),
        ),
        created_by="pytest",
        alias="production",
    )
