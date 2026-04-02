# Prompt Files

promptdb treats file-native prompt authoring as a first-class workflow. Prompts
can live in source control as YAML, JSON, or plain text and be registered
directly.

## Structured files (YAML / JSON)

Structured files capture the full `PromptSpec` shape:

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
  description: Classifies incoming support tickets.
  user_version: 2026.04.01.1
  tags:
    - support
    - classifier
  owners:
    - platform
```

Register it:

```bash
promptdb register-file prompts/support_classifier.yaml support classifier --alias production
```

Or from Python:

```python
version = client.register_file(
    path="prompts/support_classifier.yaml",
    namespace="support",
    name="classifier",
    alias="production",
)
```

### JSON format

```json
{
  "kind": "string",
  "template": "You are a {persona}. Question: {question}",
  "partial_variables": { "persona": "support analyst" },
  "metadata": {
    "title": "Support triage",
    "user_version": "1.0.0"
  }
}
```

## Plain text files

Plain text files (`.txt`, `.md`, `.prompt`, `.jinja`, `.mustache`) contain just
the template body. You must specify the `kind` explicitly:

```text
You are a research answerer.
Respond to the following question:

{question}
```

```bash
# Register as a string prompt
promptdb register-file prompts/research_answerer.md research answerer --kind string

# Register as a single-message chat prompt
promptdb register-file prompts/research_answerer.md research answerer --kind chat --message-role system
```

## Exporting

Export a resolved version bundle to disk:

```bash
promptdb export-file support/classifier:production build/classifier.json
```

From Python:

```python
from promptdb.files import save_prompt_spec, write_version_bundle

# Export just the spec
save_prompt_spec(spec, "build/classifier.yaml")

# Export the full version bundle (includes version_id, revision, aliases)
write_version_bundle(version, "build/classifier.json")
```

## Supported file extensions

| Extension       | Format     | Behavior                              |
| --------------- | ---------- | ------------------------------------- |
| `.yaml`, `.yml` | YAML       | Parsed as structured `PromptSpec`     |
| `.json`         | JSON       | Parsed as structured `PromptSpec`     |
| `.txt`, `.md`   | Plain text | Template body only, requires `--kind` |
| `.prompt`       | Plain text | Template body only, requires `--kind` |
| `.jinja`        | Plain text | Template body only, requires `--kind` |
| `.mustache`     | Plain text | Template body only, requires `--kind` |
