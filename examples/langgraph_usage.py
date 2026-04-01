"""LangGraph-oriented usage example for :mod:`promptdb`.

Purpose:
    Show how a graph node can resolve a prompt ref and materialize it into a
    LangChain prompt object.

Design:
    The example focuses on prompt resolution and materialization rather than on
    making a live model call.

Attributes:
    main: Example entry point.

Examples:
    .. code-block:: bash

        python examples/langgraph_usage.py
"""

from pathlib import Path

from promptdb import AppSettings, ChatMessage, MessageRole, PromptClient, PromptKind, PromptSpec


def main() -> None:
    """Run the LangGraph-style example.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            main()
    """
    root = Path(".demo-langgraph")
    root.mkdir(exist_ok=True)
    settings = AppSettings(
        database_url=f"sqlite:///{root / 'promptdb.sqlite3'}",
        blob_root=str(root / "blobs"),
    )
    client = PromptClient.from_env(settings)

    spec = PromptSpec(
        kind=PromptKind.CHAT,
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, template="You are a research assistant."),
            ChatMessage(role=MessageRole.HUMAN, template="{question}"),
        ],
    )
    client.register_spec(namespace="research", name="answerer", spec=spec, alias="production")

    resolved = client.get("research/answerer:production")
    langchain_prompt = resolved.as_langchain()
    rendered_value = langchain_prompt.invoke({"question": "What is PACELC?"})
    print(rendered_value)


if __name__ == "__main__":
    main()
