"""Build sources for private-function verification tests."""

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


def _lint_private_verification_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {
            issue.rule
            for test in extract_tests_from_file(test_file, repo_root)
            for issue in run_conventional_linter(test)
        }
