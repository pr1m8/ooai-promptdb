"""Allow ``python -m promptdb`` to run the CLI.

Equivalent to running the ``promptdb`` console script::

    python -m promptdb init
    python -m promptdb list
    python -m promptdb resolve support/triage:production
"""

from __future__ import annotations

from promptdb.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
