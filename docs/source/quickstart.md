# Quickstart

## Install

```bash
pdm install -G dev -G test -G docs -G dashboard -G observability -G minio -G redis
```

## Initialize a workspace

```bash
promptdb init
```

This creates a starter prompt spec and `.env.example` in the current directory.

## Register and render

```bash
promptdb register-file prompts/support_assistant.yaml demo assistant --alias production
promptdb render demo/assistant:production --var question="Where is my refund?"
```

## Python client

```python
from promptdb import PromptClient

client = PromptClient.from_env()
resolved = client.get("demo/assistant:production")
print(resolved.render_text({"question": "Where is my refund?"}))
```
