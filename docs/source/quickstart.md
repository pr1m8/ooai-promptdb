# Quickstart

## Install

From PyPI:

```bash
pip install ooai-promptdb
```

With optional extras:

```bash
pip install ooai-promptdb[minio,redis,observability]
```

For development (using PDM):

```bash
pdm install -G dev -G test -G docs -G dashboard -G observability -G minio -G redis
```

## Initialize a workspace

```bash
promptdb init
```

This creates:

- `prompts/support_assistant.yaml` — a sample chat prompt spec
- `.env.example` — default environment variables
- `build/` and `docs/` directories

## Register a prompt from a file

```bash
promptdb register-file prompts/support_assistant.yaml demo assistant --alias production
```

## Render it

```bash
promptdb render demo/assistant:production --var question="Where is my refund?"
```

## Use the Python client

```python
from promptdb import PromptClient, PromptKind, PromptMetadata

client = PromptClient.from_env()

# Register a string prompt
client.register_text(
    namespace="support",
    name="triage",
    template="You are a {persona}. Question: {question}",
    kind=PromptKind.STRING,
    alias="production",
    metadata=PromptMetadata(title="Support triage", user_version="v1"),
    partial_variables={"persona": "senior support analyst"},
)

# Resolve and render
resolved = client.get("support/triage:production")
print(resolved.render_text({"question": "Where is my refund?"}))
# => "You are a senior support analyst. Question: Where is my refund?"
```

## Materialize as a LangChain prompt

```python
langchain_prompt = resolved.as_langchain()
result = langchain_prompt.invoke({"question": "Where is my refund?"})
print(result.text)
```

## Run the API server

```bash
uvicorn promptdb.api:app --reload
```

Then visit `http://localhost:8000/docs` for the interactive OpenAPI docs.

## Configuration

All settings are read from `PROMPTDB_*` environment variables:

| Variable                    | Default                        | Description                          |
| --------------------------- | ------------------------------ | ------------------------------------ |
| `PROMPTDB_DATABASE_URL`     | `sqlite:///./promptdb.sqlite3` | SQLAlchemy database URL              |
| `PROMPTDB_BLOB_ROOT`        | `.blobs`                       | Local blob storage directory         |
| `PROMPTDB_STORAGE_BACKEND`  | `local`                        | `local` or `minio`                   |
| `PROMPTDB_API_PREFIX`       | `/api/v1`                      | API route prefix                     |
| `PROMPTDB_MINIO_ENDPOINT`   | —                              | MinIO endpoint (required if `minio`) |
| `PROMPTDB_MINIO_ACCESS_KEY` | —                              | MinIO access key                     |
| `PROMPTDB_MINIO_SECRET_KEY` | —                              | MinIO secret key                     |
| `PROMPTDB_MINIO_BUCKET`     | `promptdb`                     | MinIO bucket name                    |
| `PROMPTDB_ENABLE_METRICS`   | `false`                        | Expose Prometheus `/metrics`         |
| `PROMPTDB_ENABLE_OTEL`      | `false`                        | Enable OpenTelemetry instrumentation |
| `PROMPTDB_LOG_LEVEL`        | `INFO`                         | Root log level                       |
