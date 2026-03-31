"""Sphinx configuration for ooai-promptdb.

Purpose:
    Configure the documentation build for API references, narrative guides,
    examples, and release workflows.

Design:
    The configuration adds ``src/`` to ``sys.path`` so :mod:`~promptdb` can be
    imported without an editable install. It also enables Google-style
    docstrings through Napoleon, autosummary generation, MyST Markdown pages,
    and GitHub Pages friendly output.

Attributes:
    PROJECT_ROOT: Absolute project root.
    SRC_ROOT: Absolute source directory.
    extensions: Enabled Sphinx extensions.

Examples:
    >>> project
    'ooai-promptdb'
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

project = "ooai-promptdb"
author = "William R. Astley"
copyright = "2026, William R. Astley"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "myst_parser",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"
exclude_patterns = ["_build"]
autosummary_generate = True
autosummary_imported_members = False
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}
html_theme = "furo"
html_title = "ooai-promptdb"
html_static_path: list[str] = []
html_theme_options = {
    "source_repository": "https://github.com/pr1m8/ooai-promptdb/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}
