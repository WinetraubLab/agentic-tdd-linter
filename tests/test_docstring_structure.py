from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.docstrings import lint_test_files


class DocstringStructureTests(unittest.TestCase):
    def test_reports_missing_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A test function without a docstring is reported as missing required structure.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_docstring", rules)

    def test_reports_long_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A test name with more than five descriptive words is reported as too long.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_two_positive_integer_values_correctly() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("test_name_too_long", rules)

    def test_reports_empty_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        An empty Requirement Tested field is reported as missing requirement text.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:

                Verification Method: verify public function output

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_requirement", rules)

    def test_reports_empty_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        An empty Verification Detail field is reported as missing detail text.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_verification_detail", rules)

    def test_reports_same_line_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A Requirement Tested field with same-line text is reported as invalid formatting.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested: addition returns the expected sum.

                Verification Method: verify public function output

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_requirement_format", rules)

    def test_reports_same_line_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A Verification Detail field with same-line text is reported as invalid formatting.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail: by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_detail_format", rules)


def _lint_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


if __name__ == "__main__":
    unittest.main()
