"""Optional logging, metrics, and tracing helpers.

All dependencies are imported lazily so the base package works without
installing the ``observability`` extra. Install it to enable these features::

    pip install ooai-promptdb[observability]

Logging — uses Rich handler when available::

    from promptdb.observability import configure_logging
    configure_logging("DEBUG")

Prometheus metrics — returns an ASGI app to mount at ``/metrics``::

    from promptdb.observability import get_metrics_app
    metrics = get_metrics_app()    # None if prometheus_client not installed
    if metrics:
        app.mount("/metrics", metrics)

OpenTelemetry — instruments FastAPI and SQLAlchemy::

    from promptdb.observability import setup_otel
    setup_otel(app, engine)        # no-op if opentelemetry not installed

Enable via environment variables:

- ``PROMPTDB_ENABLE_METRICS=true`` — auto-mounts Prometheus endpoint
- ``PROMPTDB_ENABLE_OTEL=true`` — auto-instruments FastAPI + SQLAlchemy
"""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
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
        format="%(message)s" if handlers else "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="[%X]",
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
    FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    SQLAlchemyInstrumentor().instrument(engine=engine)  # type: ignore[arg-type]
