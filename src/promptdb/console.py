"""Console helpers for :mod:`promptdb`.

Purpose:
    Centralize Rich console creation so the CLI and examples use a consistent
    presentation layer.

Design:
    The module exposes a single lazily configured :class:`rich.console.Console`
    factory. The returned console is color-aware in terminals and plain enough
    for snapshot-friendly test runs.

Attributes:
    get_console: Return a configured Rich console.

Examples:
    >>> console = get_console()
    >>> console is not None
    True
"""

from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

_THEME = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "muted": "dim",
        "accent": "bold magenta",
    }
)


def get_console(*, record: bool = False) -> Console:
    """Return a configured Rich console.

    Args:
        record: Whether the console should record output for tests.

    Returns:
        Console: Rich console instance.

    Raises:
        None.

    Examples:
        >>> get_console(record=True).record
        True
    """
    return Console(theme=_THEME, soft_wrap=True, record=record)
