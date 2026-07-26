"""Test-support harnesses for conventional-linter tests."""

from __future__ import annotations

import tempfile
import textwrap
from pathlib import Path

from agentic_tdd_linter.conventional_linter.run_conventional_linter import (
    run_conventional_linter,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)


def _lint_source(source: str, filename: str = "test_sample.py") -> set[str]:
    """Return conventional-linter rules for one temporary test source."""

    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / filename
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
        return {
            issue.rule
            for test in extract_tests_from_file(test_file, repo_root)
            for issue in run_conventional_linter(test)
        }
