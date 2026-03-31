"""Package entry point for :mod:`promptdb`.

Purpose:
    Allow ``python -m promptdb`` to run the Rich-powered CLI.

Design:
    Delegates to :func:`promptdb.cli.main` and exits with its integer status
    code.

Attributes:
    None.

Examples:
    .. code-block:: bash

        python -m promptdb init
        python -m promptdb list
"""

from __future__ import annotations

from promptdb.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
