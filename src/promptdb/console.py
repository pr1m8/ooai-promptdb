"""Shared Rich console factory for CLI output.

Provides a consistently themed :class:`rich.console.Console` used by the CLI
and examples. The theme defines semantic styles (``success``, ``error``,
``warning``, ``info``, ``muted``, ``accent``) so output is visually consistent.

Usage::

    from promptdb.console import get_console

    console = get_console()
    console.print("[success]Done![/success]")
    console.print("[error]Something went wrong[/error]")

For test snapshots, pass ``record=True``::

    console = get_console(record=True)
    console.print("hello")
    output = console.export_text()
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
