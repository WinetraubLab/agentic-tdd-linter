"""Tests in this file validate `test_repository_self_lint` located at `tests/repository_health/test_repository_self_lint.py`.
`test_repository_self_lint` is responsible for proving that this repository passes its own linter.

Terms:
- `self lint`: Self lint runs the linter against this repository's own tests. For example, the integration test runs lint with this repository as the repository root.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.cli.main import main


class SelfLintTests(unittest.TestCase):
    def test_self_lint_validates_repository_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_repository_self_lint` requires `self lint` to complete with no issues for this repository.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Repository lint produces exit code `0`.
        Repository lint output contains `no issues found`.

        """

        repo_root = Path(__file__).resolve().parents[2]
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["lint", "--repo-root", str(repo_root)])

        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
