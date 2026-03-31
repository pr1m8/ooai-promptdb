"""Observability helpers for :mod:`promptdb`.

Purpose:
    Provide optional logging, Prometheus, and OpenTelemetry helpers.

Design:
    Imports are lazy so the base package stays lighter. When Rich is installed,
    logging prefers :class:`rich.logging.RichHandler` for local development.

Attributes:
    configure_logging: Configure standard logging.
    get_metrics_app: Return a Prometheus ASGI app when available.
    setup_otel: Optionally enable OTel instrumentation.

Examples:
    >>> configure_logging('INFO')
"""

from __future__ import annotations

import logging


def configure_logging(level: str = 'INFO') -> None:
    """Configure root logging.

    Args:
        level: Log level name.

    Returns:
        None.

    Raises:
        ValueError: If the level is invalid.

    Examples:
        >>> configure_logging('INFO')
    """
    handlers: list[logging.Handler] | None = []
    try:
        from rich.logging import RichHandler
    except ImportError:  # pragma: no cover - optional fallback
        handlers = None
    else:
        handlers = [RichHandler(rich_tracebacks=True, markup=True)]
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(message)s' if handlers else '%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='[%X]',
        handlers=handlers,
        force=True,
    )


def get_metrics_app() -> object | None:
    """Return a Prometheus ASGI app if the dependency is installed.

    Args:
        None.

    Returns:
        object | None: ASGI app or ``None``.

    Raises:
        None.

    Examples:
        >>> app = get_metrics_app()
        >>> app is None or callable(app)
        True
    """
    try:
        from prometheus_client import make_asgi_app
    except ImportError:
        return None
    return make_asgi_app()


def setup_otel(app: object, engine: object) -> None:
    """Optionally instrument FastAPI and SQLAlchemy with OpenTelemetry.

    Args:
        app: FastAPI application.
        engine: SQLAlchemy engine.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            setup_otel(app, engine)
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    except ImportError:
        return
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
