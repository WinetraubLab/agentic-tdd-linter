from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.cli import main


FIXTURES = Path(__file__).resolve().parent / "cli_fixtures"


class CliTests(unittest.TestCase):
    def test_valid_fixture_exits_zero(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The check command exits successfully when requested tests have no issues.

        Verification Method: verify public function output

        Verification Detail:
        by running main with the valid fixture path and capturing text output.
        """

        fixture_file = FIXTURES / "pass_test.py"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["check", "--repo-root", str(fixture_file.parent), str(fixture_file)])

        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())

    def test_invalid_fixture_exits_one(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        The check command exits with failure when requested tests have issues.

        Verification Method: verify public function output

        Verification Detail:
        by running main with an invalid fixture path and capturing text output.
        """

        fixture_file = FIXTURES / "fail_test_due_to_missing_requirement.py"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["check", "--repo-root", str(fixture_file.parent), str(fixture_file)])

        self.assertEqual(1, exit_code)
        self.assertIn("missing_requirement", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
