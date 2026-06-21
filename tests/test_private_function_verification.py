from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.docstrings import lint_test_files


class PrivateFunctionVerificationTests(unittest.TestCase):
    def test_private_verification_without_private_call(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A private verification test must call a function named like `_private_function` during the test.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `private_verification_missing_private_call` is reported for a public helper call.
        """

        rules = _lint_source(
            """
            def helper(value: str) -> str:
                return value.strip()


            def test_strips_value() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                helper returns text without surrounding whitespace.

                Verification Method: verify private function output

                Verification Detail:
                by asserting the returned stripped string.
                \"\"\"

                assert helper(" value ") == "value"
            """
        )

        self.assertIn("private_verification_missing_private_call", rules)


def _lint_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


if __name__ == "__main__":
    unittest.main()
