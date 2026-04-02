# Python Client

The `PromptClient` is the main entry point for working with promptdb from Python.

## Creating a client

```python
from promptdb import PromptClient

# From environment variables (PROMPTDB_*)
client = PromptClient.from_env()

# With explicit settings
from promptdb import AppSettings

settings = AppSettings(
    database_url="postgresql://user:pass@localhost/promptdb",
    storage_backend="minio",
    minio_endpoint="localhost:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin",
)
client = PromptClient.from_env(settings)
```

## Registering prompts

### From text

```python
from promptdb import PromptKind, PromptMetadata

# String prompt
version = client.register_text(
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
print(version.version_id)  # UUID
print(version.revision)    # 1
```

### From a spec object

```python
from promptdb import PromptSpec, ChatMessage, MessageRole

spec = PromptSpec(
    kind=PromptKind.CHAT,
    messages=[
        ChatMessage(role=MessageRole.SYSTEM, template="You are a {persona}."),
        ChatMessage(role=MessageRole.HUMAN, template="{question}"),
    ],
    partial_variables={"persona": "research assistant"},
)
version = client.register_spec(
    namespace="research",
    name="answerer",
    spec=spec,
    alias="production",
)
```

### From a file

```python
version = client.register_file(
    path="prompts/support_classifier.yaml",
    namespace="support",
    name="classifier",
    alias="production",
)
```

## Resolving prompts

Prompt references use the `namespace/name:selector` format:

```python
# By alias
version = client.resolve("support/triage:production")

# By revision number
version = client.resolve("support/triage:rev:2")

# Latest version (default)
version = client.resolve("support/triage:latest")

# By user_version label
version = client.resolve("support/triage:2026.04.01.1")

# By version UUID
version = client.resolve(f"support/triage:{version.version_id}")
```

## Rendering

```python
# Get a ResolvedPrompt wrapper
resolved = client.get("support/triage:production")

# Render a string prompt
text = resolved.render_text({"question": "Where is my refund?"})

# Render a chat prompt
messages = resolved.render_messages({"question": "Where is my refund?"})
# => [{"role": "system", "content": "You are a research assistant."}, ...]

# Or use the service-level render
result = client.render("support/triage:production", {"question": "Hello"})
print(result.text)       # for string prompts
print(result.messages)   # for chat prompts
```

## LangChain materialization

```python
resolved = client.get("research/answerer:production")

# Get a LangChain PromptTemplate or ChatPromptTemplate
langchain_prompt = resolved.as_langchain()

# Invoke it directly
value = resolved.invoke({"question": "What is PACELC?"})
print(value)
```

## Exporting

```python
# Export a version bundle to a JSON or YAML file
path = client.export_to_file("support/triage:production", "build/triage.json")
print(path)  # Path('build/triage.json')
```

## Listing versions

```python
for version in client.list_versions():
    print(f"{version.namespace}/{version.name} rev:{version.revision} "
          f"aliases={version.aliases}")
```

## Template formats

promptdb supports three template engines:

### f-string (default)

```python
spec = PromptSpec(
    kind=PromptKind.STRING,
    template="Hello {name}, welcome to {company}.",
    template_format=TemplateFormat.FSTRING,
)
```

### Jinja2

```python
from promptdb import TemplateFormat

spec = PromptSpec(
    kind=PromptKind.STRING,
    template="Hello {{ name }}, you have {{ count }} items.",
    template_format=TemplateFormat.JINJA2,
)
```

### Mustache

```python
spec = PromptSpec(
    kind=PromptKind.STRING,
    template="Hello {{ name }}, welcome.",
    template_format=TemplateFormat.MUSTACHE,
)
```

## Few-shot examples

```python
from promptdb import FewShotBlock

spec = PromptSpec(
    kind=PromptKind.STRING,
    template="Classify: {text}",
    few_shot=FewShotBlock(
        examples=[
            {"text": "I love it", "label": "positive"},
            {"text": "Terrible", "label": "negative"},
        ],
        string_template="Text: {text} -> {label}",
    ),
)
```

## Message placeholders

For chat prompts that accept dynamic message history:

```python
from promptdb import MessagePlaceholder

spec = PromptSpec(
    kind=PromptKind.CHAT,
    messages=[
        ChatMessage(role=MessageRole.SYSTEM, template="You are helpful."),
        MessagePlaceholder(variable_name="history", optional=True),
        ChatMessage(role=MessageRole.HUMAN, template="{question}"),
    ],
)
```
