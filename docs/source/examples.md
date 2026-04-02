# Examples

## Basic client usage

Register a string prompt, resolve it, and render it:

```python
from promptdb import PromptClient, PromptKind, PromptMetadata

client = PromptClient.from_env()

client.register_text(
    namespace="support",
    name="triage",
    template="You are a {persona}. Question: {question}",
    kind=PromptKind.STRING,
    alias="production",
    metadata=PromptMetadata(title="Support triage", user_version="v1"),
    partial_variables={"persona": "staff support engineer"},
)

resolved = client.get("support/triage:production")
print(resolved.render_text({"question": "Where is my refund?"}))
# => "You are a staff support engineer. Question: Where is my refund?"
```

Run it: `python examples/basic_usage.py`

## LangGraph / LangChain usage

Register a chat prompt and materialize it as a LangChain `ChatPromptTemplate`:

```python
from promptdb import (
    AppSettings, ChatMessage, MessageRole,
    PromptClient, PromptKind, PromptSpec,
)

client = PromptClient.from_env()

spec = PromptSpec(
    kind=PromptKind.CHAT,
    messages=[
        ChatMessage(role=MessageRole.SYSTEM, template="You are a research assistant."),
        ChatMessage(role=MessageRole.HUMAN, template="{question}"),
    ],
)
client.register_spec(
    namespace="research", name="answerer", spec=spec, alias="production",
)

resolved = client.get("research/answerer:production")

# Get a LangChain ChatPromptTemplate
langchain_prompt = resolved.as_langchain()

# Invoke it (returns a ChatPromptValue)
rendered_value = langchain_prompt.invoke({"question": "What is PACELC?"})
print(rendered_value)
```

Run it: `python examples/langgraph_usage.py`

## File-native prompt authoring

Keep prompts in version control as YAML:

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
  tags: [support, classifier]
  user_version: 2026.04.01.1
```

Register from the CLI:

```bash
promptdb register-file prompts/support_classifier.yaml support classifier --alias production
```

Or from Python:

```python
client.register_file(
    path="prompts/support_classifier.yaml",
    namespace="support",
    name="classifier",
    alias="production",
)
```

## Alias promotion workflow

Register two versions, then promote the newer one to production:

```python
from promptdb import PromptClient, PromptKind, PromptMetadata, PromptSpec

client = PromptClient.from_env()

# Register v1
v1 = client.register_text(
    namespace="support", name="classifier",
    template="Classify (v1): {text}",
    kind=PromptKind.STRING,
    alias="production",
    metadata=PromptMetadata(user_version="1.0.0"),
)

# Register v2
v2 = client.register_text(
    namespace="support", name="classifier",
    template="Classify (v2): {text}",
    kind=PromptKind.STRING,
    alias="candidate",
    metadata=PromptMetadata(user_version="2.0.0"),
)

# Promote v2 to production
client.service.move_alias(
    namespace="support", name="classifier",
    alias="production", version_id=v2.version_id,
)

# production now points to v2
resolved = client.get("support/classifier:production")
print(resolved.render_text({"text": "I need help"}))
# => "Classify (v2): I need help"
```

## Few-shot prompts

```python
from promptdb import PromptKind, PromptSpec, FewShotBlock

spec = PromptSpec(
    kind=PromptKind.STRING,
    template="Classify the following text: {text}",
    few_shot=FewShotBlock(
        examples=[
            {"text": "I love this product!", "label": "positive"},
            {"text": "Worst experience ever.", "label": "negative"},
            {"text": "It arrived on time.", "label": "neutral"},
        ],
        string_template="Text: {text} => {label}",
    ),
)

# Renders few-shot examples before the main template
result = spec.render_text({"text": "Great quality"})
print(result)
```
