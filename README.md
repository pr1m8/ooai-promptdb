# ooai-promptdb

[![CI](https://github.com/pr1m8/ooai-promptdb/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/ooai-promptdb/actions/workflows/ci.yml)
[![Docs](https://github.com/pr1m8/ooai-promptdb/actions/workflows/docs.yml/badge.svg)](https://github.com/pr1m8/ooai-promptdb/actions/workflows/docs.yml)
[![PyPI](https://img.shields.io/pypi/v/ooai-promptdb.svg)](https://pypi.org/project/ooai-promptdb/)
[![Python](https://img.shields.io/pypi/pyversions/ooai-promptdb.svg)](https://pypi.org/project/ooai-promptdb/)
[![License](https://img.shields.io/pypi/l/ooai-promptdb.svg)](LICENSE)

A prompt registry and runtime delivery layer for LangChain and LangGraph.

## Why this exists

Prompt-heavy LLM applications usually end up with a messy mix of inline strings, YAML files, half-versioned edits, and manual environment promotion. **promptdb** gives you a cleaner split:

- **Prompt definitions and version metadata** live in a relational database (Postgres or SQLite)
- **Large bundles and artifacts** live in blob storage (local filesystem or MinIO)
- **LangChain-compatible prompt objects** are materialized at runtime
- **Aliases** like `production` or `staging` point at immutable versions — promotion is an alias move, not a code change
- **Files remain first-class** — prompts can stay in source control as YAML, JSON, or plain text

## Install

```bash
pip install ooai-promptdb
```

With optional extras:

```bash
pip install ooai-promptdb[minio,redis,observability]
```

## Quick start

### Python client

```python
from promptdb import PromptClient, PromptKind, PromptMetadata

client = PromptClient.from_env()

# Register a prompt
client.register_text(
    namespace="support",
    name="triage",
    template="You are a {persona}. Question: {question}",
    kind=PromptKind.STRING,
    alias="production",
    metadata=PromptMetadata(
        title="Support triage",
        user_version="2026.04.01.1",
        tags=["support", "triage"],
    ),
    partial_variables={"persona": "senior support analyst"},
)

# Resolve and render
resolved = client.get("support/triage:production")
print(resolved.render_text({"question": "Where is my refund?"}))
# => "You are a senior support analyst. Question: Where is my refund?"
```

### LangChain materialization

```python
langchain_prompt = resolved.as_langchain()
result = langchain_prompt.invoke({"question": "Where is my refund?"})
```

### Prompt files

Keep prompts in source control as YAML:

```yaml
# prompts/support_classifier.yaml
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
  user_version: 2026.04.01.1
  tags: [support, classification]
```

```python
version = client.register_file(
    path="prompts/support_classifier.yaml",
    namespace="support",
    name="classifier",
    alias="production",
)
```

### CLI

```bash
promptdb init                        # scaffold a workspace
promptdb list                        # list all versions
promptdb register-file prompts/support_classifier.yaml support classifier --alias production
promptdb resolve support/classifier:production
promptdb render support/classifier:production --var ticket_text="Refund missing"
promptdb export-file support/classifier:production build/classifier.json
```

### HTTP API

```bash
uvicorn promptdb.api:app --reload
```

```bash
# Register
curl -X POST http://localhost:8000/api/v1/prompts/register \
  -H 'Content-Type: application/json' \
  -d '{"namespace":"support","name":"triage","alias":"production","spec":{"kind":"string","template":"Hello {name}"}}'

# Resolve
curl http://localhost:8000/api/v1/prompts/support/triage/resolve?selector=production

# Render
curl -X POST http://localhost:8000/api/v1/prompts/support/triage/render?selector=production \
  -H 'Content-Type: application/json' \
  -d '{"variables":{"name":"Will"}}'
```

## Architecture

```text
files / CLI / API / dashboard
          |
      PromptClient (client.py)  — ergonomic facade
          |
      PromptService (service.py) — orchestrates workflows
       /          \
  PromptRepository   BlobStore adapters
  (db.py)            (storage.py)
  SQLAlchemy ORM     LocalBlobStore | MinioBlobStore
```

### Prompt references

Compact `namespace/name:selector` format with resolution order:

1. Version UUID
2. `rev:N` revision
3. Alias (`production`, `staging`, `latest`)
4. User version label (`2026.04.01.1`)
5. `latest` fallback (highest revision)

### Features

- String and chat prompts with f-string, Jinja2, and mustache templates
- Partial variables, message placeholders, and few-shot examples
- Immutable versions with movable aliases for environment promotion
- File-native import/export (YAML, JSON, plain text)
- Relational asset metadata for blob-backed exports
- FastAPI with OpenAPI docs, Rich CLI, Streamlit dashboard scaffold
- Prometheus metrics and OpenTelemetry instrumentation (optional)
- Alembic migrations for schema evolution
- `py.typed` marker for downstream type checking

## Configuration

All settings are read from `PROMPTDB_*` environment variables:

| Variable                    | Default                        | Description                    |
| --------------------------- | ------------------------------ | ------------------------------ |
| `PROMPTDB_DATABASE_URL`     | `sqlite:///./promptdb.sqlite3` | SQLAlchemy database URL        |
| `PROMPTDB_BLOB_ROOT`        | `.blobs`                       | Local blob storage directory   |
| `PROMPTDB_STORAGE_BACKEND`  | `local`                        | `local` or `minio`             |
| `PROMPTDB_MINIO_ENDPOINT`   | —                              | MinIO endpoint                 |
| `PROMPTDB_MINIO_ACCESS_KEY` | —                              | MinIO access key               |
| `PROMPTDB_MINIO_SECRET_KEY` | —                              | MinIO secret key               |
| `PROMPTDB_ENABLE_METRICS`   | `false`                        | Prometheus `/metrics` endpoint |
| `PROMPTDB_ENABLE_OTEL`      | `false`                        | OpenTelemetry instrumentation  |

## Development

```bash
pdm install -G dev -G test -G docs -G dashboard -G observability -G minio -G redis
make test          # run all tests
make lint          # ruff check
make typecheck     # mypy
make docs          # sphinx build
make all           # lint + typecheck + test + docs
```

## Documentation

- [GitHub Pages](https://pr1m8.github.io/ooai-promptdb/)
- [ReadTheDocs](https://ooai-promptdb.readthedocs.io) (when configured)

## License

MIT
