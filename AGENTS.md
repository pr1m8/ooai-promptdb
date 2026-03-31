# AGENTS.md

## Purpose

This repository implements **promptdb**, a prompt registry and runtime delivery layer for LangChain and LangGraph applications. It stores prompt metadata, versions, aliases, and relational asset metadata in SQL databases via SQLAlchemy and Alembic, while storing larger bundle and export artifacts in local blob storage or MinIO.

This file is intended for coding agents and contributors making changes inside the repository.

## Architecture at a glance

- `src/promptdb/domain.py`
  - Core Pydantic domain models such as `PromptSpec`, `PromptRef`, `ResolvedPrompt`, `PromptVersionView`, `PromptMetadata`, and related enums.
- `src/promptdb/repository.py`
  - SQLAlchemy ORM repository layer for prompts, versions, aliases, and relational asset records.
- `src/promptdb/service.py`
  - Main application service. Coordinates prompt registration, versioning, alias movement, rendering, export, file ingestion, and asset listing.
- `src/promptdb/client.py`
  - Ergonomic Python client wrapper around the service/API concepts.
- `src/promptdb/api.py`
  - FastAPI app exposing prompt registration, resolution, rendering, listing, and export flows.
- `src/promptdb/storage.py`
  - Blob adapters for local filesystem storage and MinIO.
- `src/promptdb/cli.py`
  - Rich-powered CLI entry point.
- `alembic/`
  - Relational schema migrations.
- `docs/`
  - Sphinx docs.
- `tests/`
  - Unit, integration, and e2e coverage.
- `prompts/`
  - Example prompt files in text, markdown, YAML, and similar formats.

## Development principles

1. Keep **domain models**, **I/O adapters**, and **service orchestration** separate.
2. Prefer **typed Pydantic models** for public inputs/outputs.
3. Keep **blob storage** metadata relationally queryable via SQLAlchemy models and Alembic migrations.
4. Avoid hidden network or filesystem side effects at import time.
5. Make local development work with SQLite + local blob storage first, then support Postgres + MinIO.
6. Preserve backward compatibility for prompt references such as `namespace/name:selector` where possible.
7. Keep docs, examples, and tests in sync with behavior changes.

## Coding standards

### Python

- Target Python `>=3.13`.
- Use full type hints.
- Use Google-style docstrings compatible with Sphinx Napoleon.
- Public modules, classes, and functions should include meaningful examples where practical.
- Prefer pure functions in normalization and rendering code when possible.

### Pydantic

- Use Pydantic v2 idioms.
- Keep validation logic near the model that owns the invariant.
- Avoid leaking raw ORM objects into public APIs.

### SQLAlchemy and Alembic

- Schema changes must be reflected in:
  - ORM models
  - repository/service usage
  - Alembic migrations
  - tests when behavior changes
- Relational metadata for blob-backed assets belongs in the database even when file contents live in MinIO.

### CLI and UX

- Use Rich for CLI output and user-facing diagnostics.
- Keep command names short and predictable.
- Prefer composable commands over overly magical flows.

## Testing expectations

Before considering a change complete, run as many of these as applicable:

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src pytest tests/test_unit.py -q
PYTHONPATH=src pytest tests/test_integration.py -q
PYTHONPATH=src pytest tests/test_e2e.py -q
python -m compileall src
```

If docs or CLI output changed, also run:

```bash
pdm run docs
pdm run promptdb --help
```

## Common change workflows

### Add a new prompt capability

1. Extend `PromptKind`, `PromptSpec`, or related domain types.
2. Update render/materialization behavior.
3. Update file import/export logic if applicable.
4. Add tests for:
   - serialization
   - rendering
   - resolution/versioning
   - API or CLI integration if exposed there
5. Update docs and examples.

### Add a new relational asset kind

1. Extend the asset enum/model.
2. Add migration if schema changes are needed.
3. Update repository and service flows.
4. Add integration coverage for creation and lookup.
5. Document how it maps to blob storage.

### Add a new CLI command

1. Implement the command in `src/promptdb/cli.py`.
2. Use Rich console rendering for output.
3. Add CLI tests.
4. Add usage examples to the README and docs if the command is user-facing.

## Things to avoid

- Do not store large prompt bundles only in SQL rows when they belong in blob storage.
- Do not add runtime-only computed fields to persisted serialized payloads unless they are intentionally part of the contract.
- Do not silently change selector semantics like `latest`, `production`, or `rev:<n>`.
- Do not introduce mandatory external-service coupling for local tests.

## Release hygiene

When changing behavior that affects consumers, review:

- `README.md`
- `docs/`
- `.github/workflows/`
- `pyproject.toml`
- Alembic migrations
- examples and test coverage

## Recommended first reads

1. `README.md`
2. `src/promptdb/domain.py`
3. `src/promptdb/service.py`
4. `src/promptdb/api.py`
5. `tests/`
