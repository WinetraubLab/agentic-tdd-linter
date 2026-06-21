from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.cli import main


FISHFOOD_CHECK_ARGS = ["check", "--all"]


class SelfLintTests(unittest.TestCase):
    def test_fishfood_validates_repository_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Fishfood validates repository tests.

        Verification Method: verify public function output

        Verification Detail:
        Command output includes success.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([*FISHFOOD_CHECK_ARGS, "--repo-root", str(REPO_ROOT)])

        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
