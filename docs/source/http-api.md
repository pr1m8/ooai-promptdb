# HTTP API

promptdb ships a FastAPI application with endpoints for prompt registration,
resolution, rendering, alias management, and export.

## Running the server

```bash
uvicorn promptdb.api:app --reload
```

Interactive docs are available at `http://localhost:8000/docs`.

## Endpoints

All endpoints are under the `/api/v1` prefix by default.

### Register a prompt

```
POST /api/v1/prompts/register
```

```json
{
  "namespace": "support",
  "name": "triage",
  "alias": "production",
  "created_by": "will",
  "spec": {
    "kind": "string",
    "template": "You are a {persona}. Question: {question}",
    "partial_variables": { "persona": "support analyst" },
    "metadata": {
      "title": "Support triage",
      "user_version": "v1"
    }
  }
}
```

Returns the created `PromptVersionView`.

### Resolve a prompt

```
GET /api/v1/prompts/{namespace}/{name}/resolve?selector=production
```

The `selector` parameter accepts aliases (`production`), revision refs
(`rev:2`), user version labels, or version UUIDs. Defaults to `latest`.

### Render a prompt

```
POST /api/v1/prompts/{namespace}/{name}/render?selector=production
```

```json
{
  "variables": { "question": "Where is my refund?" }
}
```

Returns a `PromptRenderResult` with either `text` (string prompts) or
`messages` (chat prompts).

### Move an alias

```
POST /api/v1/prompts/{namespace}/{name}/aliases/{alias}
```

```json
{
  "alias": "production",
  "version_id": "uuid-of-target-version"
}
```

### List all versions

```
GET /api/v1/versions
```

### List assets for a version

```
GET /api/v1/prompts/{namespace}/{name}/assets?selector=production
```

### Export a version bundle

```
GET /api/v1/exports/{namespace}/{name}/{selector}
```

Exports the version to blob storage and returns the asset metadata.

## App factory

The `create_app()` function accepts optional `AppSettings` for testing or
custom configuration:

```python
from promptdb.api import create_app
from promptdb.settings import AppSettings

app = create_app(AppSettings(
    database_url="postgresql://...",
    storage_backend="minio",
    minio_endpoint="localhost:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin",
))
```

## Observability

When `PROMPTDB_ENABLE_METRICS=true`, a Prometheus metrics endpoint is mounted
at `/metrics`.

When `PROMPTDB_ENABLE_OTEL=true`, OpenTelemetry instrumentation is wired for
both FastAPI and SQLAlchemy.
