Architecture
============

The scaffold includes:

- a typed prompt domain model with metadata, user-facing version labels, partials, placeholders, and few-shot support
- SQLAlchemy persistence for logical prompts, immutable versions, and movable aliases
- FastAPI endpoints for registration, alias promotion, resolution, rendering, listing, and export
- optional Streamlit dashboard support
- local and MinIO-backed blob storage
- observability hooks for logging, Prometheus, and OpenTelemetry

Relational blob linkage
-----------------------

Blob objects in local storage or MinIO are represented relationally in the ``prompt_assets`` table. Each asset row points to a concrete prompt version and stores the backend, bucket, object key, MIME type, byte size, and checksum. This keeps operational metadata queryable through Postgres while leaving large payloads in object storage.
