"""Basic usage example for :mod:`promptdb`.

Purpose:
    Show local prompt registration, resolution, and rendering with the
    ergonomic client facade.

Design:
    Uses a local SQLite database and local blob storage by default.

Attributes:
    main: Example entry point.

Examples:
    .. code-block:: bash

        python examples/basic_usage.py
"""

from __future__ import annotations

from promptdb import PromptClient, PromptKind, PromptMetadata


def main() -> None:
    """Run the basic example.

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


if __name__ == "__main__":
    main()
