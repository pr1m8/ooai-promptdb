# ooai-promptdb

[![CI](https://github.com/pr1m8/ooai-promptdb/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/ooai-promptdb/actions/workflows/ci.yml)
[![Docs](https://github.com/pr1m8/ooai-promptdb/actions/workflows/docs.yml/badge.svg)](https://github.com/pr1m8/ooai-promptdb/actions/workflows/docs.yml)
[![PyPI](https://img.shields.io/pypi/v/ooai-promptdb.svg)](https://pypi.org/project/ooai-promptdb/)
[![Python](https://img.shields.io/pypi/pyversions/ooai-promptdb.svg)](https://pypi.org/project/ooai-promptdb/)
[![License](https://img.shields.io/pypi/l/ooai-promptdb.svg)](LICENSE)
[![Coverage](https://codecov.io/gh/pr1m8/ooai-promptdb/branch/main/graph/badge.svg)](https://codecov.io/gh/pr1m8/ooai-promptdb)

A prompt registry and runtime delivery layer for LangChain and LangGraph, with relational versioning in Postgres or SQLite, blob-backed assets in local storage or MinIO, a FastAPI API, a Rich CLI, a Streamlit dashboard, Alembic migrations, and a testable developer workflow.

## Why this package exists

Prompt-heavy applications usually end up with a messy mix of inline strings, YAML files, half-versioned edits, and manual environment promotion. `ooai-promptdb` gives you a cleaner split:

- **Prompt definitions and version metadata** live in a relational database.
- **Large bundles and artifacts** live in local blob storage or MinIO.
- **LangChain-compatible prompt objects** can be materialized at runtime.
- **Aliases like `production` or `staging`** point at immutable versions.
- **Files remain first-class** so prompts can stay in source control.

## Features

- typed prompt specs with metadata, user-facing version labels, tags, descriptions, partial variables, placeholders, and lightweight few-shot support
- string and chat prompt rendering with ergonomic selectors such as `support/classifier:production`
- file-native import and export for plain text, YAML, and JSON prompt specs
- relational versioning, aliases, and asset metadata with SQLAlchemy and Alembic
- local blob storage plus a MinIO adapter for export bundles and attachments
- FastAPI service surface for registration, resolution, rendering, export, and asset listing
- Rich-powered CLI for local operations
- Streamlit dashboard scaffold
- unit, integration, and e2e tests with coverage support
- Sphinx docs, examples, GitHub Actions workflows, and Read the Docs configuration

## Architecture

```text
files / CLI / API / dashboard
            |
        prompt service
       /               relational store    blob store
(SQLAlchemy/Alembic) (local or MinIO)
            |
      LangChain materialization
            |
     LangGraph or app runtime
```

## Quick start

### Install

```bash
pdm install -G dev -G test -G docs -G dashboard -G observability -G minio -G redis
```

### Bootstrap a workspace

```bash
pdm run promptdb init
```

That generates a small local workspace with:

- `prompts/support_assistant.yaml`
- `.env.example`
- `build/`

### Run the API

```bash
pdm run uvicorn promptdb.api:app --reload
```

### Run the dashboard

```bash
pdm run streamlit run src/promptdb/dashboard_streamlit/app.py
```

### Run tests with coverage

```bash
pdm run pytest --cov=src/promptdb --cov-report=term-missing --cov-report=xml
```

## Make targets

A small `Makefile` is included so you do not have to remember the common PDM commands.

```bash
make install
make test
make cov
make docs
make api
make dashboard
make lint
make format
make all
```

## Developer usage

```python
from promptdb import PromptClient, PromptKind, PromptMetadata

client = PromptClient.from_env()

client.register_text(
    namespace="support",
    name="triage",
    template="You are a {persona}. Question: {question}",
    kind=PromptKind.STRING,
    alias="production",
    metadata=PromptMetadata(
        title="Support triage",
        description="Primary support triage prompt.",
        user_version="2026.04.01.1",
        tags=["support", "triage"],
    ),
    partial_variables={"persona": "senior support analyst"},
)

resolved = client.get("support/triage:production")
print(resolved.render_text({"question": "Where is my refund?"}))
```

## Structured prompt files

You can keep prompts in source control as YAML or JSON and register them directly.

```yaml
kind: chat
template_format: f-string
messages:
  - role: system
    template: You are a {persona} classifier for {company}.
  - role: human
    template: "{ticket_text}"
partial_variables:
  company: OOAI
metadata:
  title: Support classifier
  description: Support ticket classification prompt.
  user_version: 2026.04.01.1
  tags: [support, classification]
```

```python
from promptdb import PromptClient

client = PromptClient.from_env()
version = client.register_file(
    path="prompts/support_classifier.yaml",
    namespace="support",
    name="classifier",
    alias="production",
)
print(version.version_id)
```

## CLI

```bash
promptdb init
promptdb list
promptdb resolve support/classifier:production
promptdb render support/classifier:production --var ticket_text="Refund missing"
promptdb register-file prompts/support_classifier.yaml support classifier --alias production
promptdb export-file support/classifier:production build/classifier.json
```

## Relational assets + MinIO

Prompt exports and attachments can live in local blob storage or MinIO, but they are also tracked relationally through the `prompt_assets` table. That table stores the owning prompt version, storage backend, bucket, object key, content type, byte size, and checksum so the API can query assets without scanning object storage.

Run Alembic migrations before production startup:

```bash
alembic upgrade head
```

## Docs

Build docs locally:

```bash
pdm install -G docs
pdm run docs
```

The repository also includes:

- `.github/workflows/ci.yml` for lint, types, tests, coverage, and docs
- `.github/workflows/docs.yml` for documentation builds and Pages deployment
- `.github/workflows/release.yml` for trusted PyPI releases on tags
- `.readthedocs.yaml` for Read the Docs builds

## Coverage

Coverage is configured through `pytest-cov` and `coverage.py`. Local coverage output goes to the terminal and `coverage.xml`, and CI uploads the XML artifact. The default source target is `src/promptdb`.

## Project status

This is a strong scaffold and a runnable starting point, not a finished enterprise platform. The main extension areas are:

- broader LangChain prompt-class round-tripping
- more complete MinIO presign and multipart flows
- richer dashboard UX
- stronger auth, multi-user, and RBAC workflows

## License

MIT
