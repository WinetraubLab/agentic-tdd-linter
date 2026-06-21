from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.docstrings import lint_test_files


class ClassificationTests(unittest.TestCase):
    def test_accepts_happy_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts happy path as a valid test path classification.

        Verification Method: verify public function output

        Verification Detail:
        by linting a generated test file and asserting no invalid path rule is returned.
        """

        rules = _lint_source(_source_with_classification(test_path="happy path"))

        self.assertNotIn("invalid_test_path", rules)

    def test_accepts_failure_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts failure path as a valid test path classification.

        Verification Method: verify public function output

        Verification Detail:
        by linting a generated test file and asserting no invalid path rule is returned.
        """

        rules = _lint_source(_source_with_classification(test_path="failure path"))

        self.assertNotIn("invalid_test_path", rules)

    def test_reports_invalid_test_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter reports unsupported test path classifications as invalid test paths.

        Verification Method: verify private function output

        Verification Detail:
        by linting a generated test file and asserting the returned rule.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: edge path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_test_path", rules)

    def test_accepts_public_output(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts "public function output" as a valid verification method.

        Verification Method: verify public function output

        Verification Detail:
        by linting a generated test file and asserting no invalid method rule is returned.
        """

        rules = _lint_source(
            _source_with_classification(verification_method="verify public function output")
        )

        self.assertNotIn("invalid_verification_method", rules)

    def test_accepts_private_output(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts "private function output" as a valid verification method.

        Verification Method: verify public function output

        Verification Detail:
        by linting a generated test file and asserting no invalid method rule is returned.
        """

        rules = _lint_source(
            _source_with_classification(
                verification_method="verify private function output",
                call="_add_values(1, 1)",
            )
        )

        self.assertNotIn("invalid_verification_method", rules)

    def test_accepts_visual_inspection(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts "visual inspection by user" as a valid verification method.

        Verification Method: verify public function output

        Verification Detail:
        by linting a generated test file and asserting no invalid method rule is returned.
        """

        rules = _lint_source(
            _source_with_classification(
                verification_method="visual inspection by user",
                verification_detail="by writing tests/artifacts/addition.png for review.",
                inspection_instructions="Confirm the image shows the expected addition result.",
                call="write_visual_inspection_artifact()",
            )
        )

        self.assertNotIn("invalid_verification_method", rules)

    def test_reports_invalid_method(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter reports unsupported verification methods as invalid classifications.

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

                Verification Method: verify database state

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_method", rules)


def _lint_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


def _source_with_classification(
    *,
    test_path: str = "happy path",
    verification_method: str = "verify public function output",
    verification_detail: str = "by asserting the returned numeric total.",
    inspection_instructions: str | None = None,
    call: str = "assert 1 + 1 == 2",
) -> str:
    inspection_block = ""
    if inspection_instructions is not None:
        inspection_block = f"""

                Inspection Instructions:
                {inspection_instructions}"""

    return f"""
            def _add_values(left: int, right: int) -> int:
                return left + right


            def write_visual_inspection_artifact() -> None:
                return None


            def test_adds_values() -> None:
                \"\"\"Test Path: {test_path}

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: {verification_method}

                Verification Detail:
                {verification_detail}{inspection_block}
                \"\"\"

                {call}
            """


if __name__ == "__main__":
    unittest.main()
