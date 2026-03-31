"""CLI tests for :mod:`promptdb`.

Purpose:
    Verify the Rich-powered CLI covers initialization and common prompt flows.

Design:
    The tests invoke :func:`promptdb.cli.main` directly with temporary
    environment configuration.

Attributes:
    None.

Examples:
    >>> True
    True
"""

from __future__ import annotations

from pathlib import Path

import pytest

from promptdb.cli import main


@pytest.mark.unit
def test_init_creates_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure ``promptdb init`` creates starter files.

    Args:
        tmp_path: Temporary directory.
        monkeypatch: Pytest monkeypatch fixture.
        capsys: Output capture fixture.

    Returns:
        None.

    Raises:
        AssertionError: If outputs are missing.

    Examples:
        .. code-block:: python

            test_init_creates_workspace(tmp_path, monkeypatch, capsys)
    """
    exit_code = main(["init", "--root", str(tmp_path)])
    assert exit_code == 0
    assert (tmp_path / "prompts" / "support_assistant.yaml").exists()
    assert (tmp_path / ".env.example").exists()
    out = capsys.readouterr().out
    assert "Workspace ready" in out


@pytest.mark.unit
def test_register_and_list_with_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure CLI registration and listing succeed.

    Args:
        tmp_path: Temporary directory.
        monkeypatch: Environment patch fixture.
        capsys: Output capture fixture.

    Returns:
        None.

    Raises:
        AssertionError: If command output is missing expected values.

    Examples:
        .. code-block:: python

            test_register_and_list_with_cli(tmp_path, monkeypatch, capsys)
    """
    db_path = tmp_path / "cli.sqlite3"
    blob_root = tmp_path / ".blobs"
    monkeypatch.setenv("PROMPTDB_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PROMPTDB_BLOB_ROOT", str(blob_root))

    main(["init", "--root", str(tmp_path)])
    prompt_path = tmp_path / "prompts" / "support_assistant.yaml"
    register_exit = main(
        ["register-file", str(prompt_path), "demo", "assistant", "--alias", "production"]
    )
    assert register_exit == 0
    assert main(["list"]) == 0
    output = capsys.readouterr().out
    assert "demo/assistant:production" in output or "demo" in output


@pytest.mark.unit
def test_render_with_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure CLI rendering succeeds.

    Args:
        tmp_path: Temporary directory.
        monkeypatch: Environment patch fixture.
        capsys: Output capture fixture.

    Returns:
        None.

    Raises:
        AssertionError: If rendered content is missing.

    Examples:
        .. code-block:: python

            test_render_with_cli(tmp_path, monkeypatch, capsys)
    """
    db_path = tmp_path / "cli-render.sqlite3"
    blob_root = tmp_path / ".blobs"
    monkeypatch.setenv("PROMPTDB_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PROMPTDB_BLOB_ROOT", str(blob_root))

    main(["init", "--root", str(tmp_path)])
    prompt_path = tmp_path / "prompts" / "support_assistant.yaml"
    main(["register-file", str(prompt_path), "demo", "assistant", "--alias", "production"])
    render_exit = main(
        ["render", "demo/assistant:production", "--var", "question=Where is my refund?"]
    )
    assert render_exit == 0
    output = capsys.readouterr().out
    assert "Where is my refund?" in output
