from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.cli import main


class SelfLintTests(unittest.TestCase):
    def test_linter_accepts_project_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The linter accepts this repository's own test suite.

        Verification Method: verify public function output

        Verification Detail:
        by running the check command against all project tests and asserting success.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["check", "--repo-root", str(REPO_ROOT), "--all"])

        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
