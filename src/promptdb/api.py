"""FastAPI application for :mod:`promptdb`.

Purpose:
    Expose prompt registration, alias movement, resolution, rendering, listing,
    and export workflows over HTTP.

Design:
    The app factory wires settings, storage, sessions, and observability. Local
    development creates database tables on startup; production should still run
    Alembic migrations.

Attributes:
    app: Default FastAPI application.
    create_app: App factory.

Examples:
    >>> create_app().title
    'promptdb'
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from promptdb.db import create_all, create_session_factory
from promptdb.domain import (
    AliasMove,
    PromptAssetView,
    PromptRef,
    PromptRegistration,
    PromptRenderResult,
    PromptVersionView,
)
from promptdb.observability import configure_logging, get_metrics_app
from promptdb.service import PromptService
from promptdb.settings import AppSettings
from promptdb.storage import LocalBlobStore, MinioBlobStore


class RenderRequest(BaseModel):
    """Request model for prompt rendering.

    Args:
        variables: Runtime variables.

    Returns:
        RenderRequest: Render request.

    Raises:
        None.

    Examples:
        >>> RenderRequest(variables={'name': 'Will'}).variables['name']
        'Will'
    """

    model_config = ConfigDict(extra='forbid')

    variables: dict[str, Any] = Field(default_factory=dict)


def build_service(settings: AppSettings) -> PromptService:
    """Build a configured prompt service.

    Args:
        settings: Application settings.

    Returns:
        PromptService: Configured service.

    Raises:
        ValueError: If storage settings are incomplete.

    Examples:
        >>> build_service(AppSettings(database_url='sqlite:///./promptdb.sqlite3')) is not None
        True
    """
    session_factory = create_session_factory(settings.database_url)
    blob_store: LocalBlobStore | MinioBlobStore
    if settings.storage_backend == 'local':
        blob_store = LocalBlobStore(settings.blob_root)
    elif settings.storage_backend == 'minio':
        has_creds = (
            settings.minio_endpoint
            and settings.minio_access_key
            and settings.minio_secret_key
        )
        if not has_creds:
            raise ValueError(
                'MinIO storage requires endpoint, access key, '
                'and secret key.',
            )
        blob_store = MinioBlobStore(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
        )
    else:
        raise ValueError(
            f'Unsupported storage_backend: '
            f'{settings.storage_backend}',
        )
    return PromptService(session_factory, blob_store)


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create the FastAPI application.

    Args:
        settings: Optional explicit settings.

    Returns:
        FastAPI: Configured app.

    Raises:
        None.

    Examples:
        >>> create_app().title
        'promptdb'
    """
    resolved_settings = settings or AppSettings()
    configure_logging(resolved_settings.log_level)
    prefix = resolved_settings.api_prefix

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        create_all(resolved_settings.database_url)
        yield

    app = FastAPI(
        title='promptdb', version='0.1.0', lifespan=_lifespan,
    )
    service = build_service(resolved_settings)
    app.state.promptdb_service = service
    app.state.promptdb_settings = resolved_settings

    if resolved_settings.enable_metrics:
        metrics_app = get_metrics_app()
        if metrics_app is not None:
            app.mount('/metrics', metrics_app)

    @app.exception_handler(LookupError)
    def _lookup_handler(
        _: Request, exc: LookupError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404, content={'detail': str(exc)},
        )

    @app.post(f'{prefix}/prompts/register')
    def register_prompt(
        payload: PromptRegistration,
    ) -> PromptVersionView:
        return service.register(payload)

    @app.post(
        f'{prefix}/prompts/{{namespace}}/{{name}}'
        f'/aliases/{{alias}}',
    )
    def move_alias(
        namespace: str, name: str, alias: str,
        payload: AliasMove,
    ) -> PromptVersionView:
        try:
            return service.move_alias(
                namespace=namespace, name=name,
                alias=alias, version_id=payload.version_id,
            )
        except LookupError as exc:
            raise HTTPException(
                status_code=404, detail=str(exc),
            ) from exc

    @app.get(f'{prefix}/prompts/{{namespace}}/{{name}}/resolve')
    def resolve_prompt(
        namespace: str, name: str, selector: str = 'latest',
    ) -> PromptVersionView:
        return service.resolve(
            PromptRef(
                namespace=namespace, name=name, selector=selector,
            ),
        )

    @app.post(f'{prefix}/prompts/{{namespace}}/{{name}}/render')
    def render_prompt(
        namespace: str, name: str,
        payload: RenderRequest, selector: str = 'latest',
    ) -> PromptRenderResult:
        return service.render(
            PromptRef(
                namespace=namespace, name=name, selector=selector,
            ),
            payload.variables,
        )

    @app.get(f'{prefix}/versions')
    def list_versions() -> list[PromptVersionView]:
        return service.list_versions()

    @app.get(f'{prefix}/prompts/{{namespace}}/{{name}}/assets')
    def list_prompt_assets(
        namespace: str, name: str, selector: str = 'latest',
    ) -> list[PromptAssetView]:
        return service.list_assets(
            PromptRef(
                namespace=namespace, name=name, selector=selector,
            ),
        )

    @app.get(
        f'{prefix}/exports/{{namespace}}/{{name}}/{{selector}}',
    )
    def export_version(
        namespace: str, name: str, selector: str,
    ) -> PromptAssetView:
        version = service.resolve(
            PromptRef(
                namespace=namespace, name=name, selector=selector,
            ),
        )
        return service.export_bundle(version)

    return app


app = create_app()
