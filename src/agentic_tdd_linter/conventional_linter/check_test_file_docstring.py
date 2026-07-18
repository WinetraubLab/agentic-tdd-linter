"""Check that Python test files begin with module documentation."""

from __future__ import annotations

import ast
from pathlib import Path

from .run_conventional_linter import LintIssue


def check_test_file_docstring(
    test_file_path: Path,
    repo_root: Path,
) -> list[LintIssue]:
    """Return one issue when a Python test file lacks a module docstring."""

    path = Path(test_file_path).resolve()
    if path.suffix != ".py":
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    if ast.get_docstring(tree):
        return []
    return [
        LintIssue(
            path=_relative_path(path, repo_root),
            test_name="<module>",
            line=1,
            rule="missing_file_docstring",
            message="Python test files must begin with a module docstring",
        )
    ]


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.relative_to(Path(repo_root).resolve())
    except ValueError:
        return path
