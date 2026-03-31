# Examples

## Basic client usage

See `examples/basic_usage.py`.

## LangGraph usage

See `examples/langgraph_usage.py`.

## File-native prompt authoring

Prompt specs can live in source control as JSON or YAML and be loaded with:

```python
from promptdb import PromptClient

client = PromptClient.from_env()
client.register_file(
    path="prompts/support_classifier.yaml",
    namespace="support",
    name="classifier",
    alias="production",
)
```
