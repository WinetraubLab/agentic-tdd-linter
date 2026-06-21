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
        by asserting `missing_docstring` is reported for a test with no docstring.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_docstring", rules)

    def test_reports_missing_test_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A docstring without Test Path is reported as missing required structure.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_test_path` is reported when `Test Path` is absent.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"
                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_test_path", rules)

    def test_reports_empty_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        An empty Requirement Tested field is reported as missing requirement text.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_requirement` is reported when `Requirement Tested` is empty.
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

    def test_reports_missing_method(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A docstring without Verification Method is reported as missing required structure.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_verification_method` is reported when the method field is absent.
        """

        rules = _lint_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_verification_method", rules)

    def test_reports_empty_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        An empty Verification Detail field is reported as missing detail text.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_verification_detail` is reported when the detail field is empty.
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

    def test_reports_missing_inspection_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A visual inspection test without an artifact path is reported as missing required structure.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_visual_inspection_artifact` is reported when no image path is named.
        """

        rules = _lint_source(
            _visual_inspection_source(
                verification_detail="by writing an image for review.",
            )
        )

        self.assertIn("missing_visual_inspection_artifact", rules)

    def test_reports_missing_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A visual inspection test without Inspection Instructions is reported as missing required structure.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_inspection_instructions` is reported when instructions are absent.
        """

        rules = _lint_source(_visual_inspection_source(inspection_instructions=None))

        self.assertIn("missing_inspection_instructions", rules)

    def test_reports_missing_visual_helper(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A visual inspection test without the artifact helper call is reported as missing required structure.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `missing_visual_inspection_helper` is reported when the helper is not called.
        """

        rules = _lint_source(
            _visual_inspection_source(call="pass")
        )

        self.assertIn("missing_visual_inspection_helper", rules)

    def test_reports_long_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A test name with more than five descriptive words is reported as too long.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `test_name_too_long` is reported for a seven-word test name.
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

    def test_reports_same_line_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A Requirement Tested field with same-line text is reported as invalid formatting.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `invalid_requirement_format` is reported for same-line requirement text.
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
        by asserting `invalid_verification_detail_format` is reported for same-line detail text.
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

    def test_reports_same_line_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        A visual inspection test with same-line Inspection Instructions is reported as invalid formatting.

        Verification Method: verify private function output

        Verification Detail:
        by asserting `invalid_inspection_instructions_format` is reported for same-line instructions.
        """

        rules = _lint_source(
            _visual_inspection_source(
                inspection_instructions="Inspection Instructions: Confirm the image shows the expected addition result.",
            )
        )

        self.assertIn("invalid_inspection_instructions_format", rules)


def _lint_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


def _visual_inspection_source(
    *,
    verification_detail: str = "by writing tests/artifacts/addition.png for review.",
    inspection_instructions: str | None = (
        "Inspection Instructions:\n"
        "                Confirm the image shows the expected addition result."
    ),
    call: str = "write_visual_inspection_artifact()",
) -> str:
    instructions_block = ""
    if inspection_instructions is not None:
        instructions_block = f"\n\n                {inspection_instructions}"

    return f"""
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                renderer writes an image that shows the expected addition result.

                Verification Method: visual inspection by user

                Verification Detail:
                {verification_detail}{instructions_block}
                \"\"\"

                {call}
            """


if __name__ == "__main__":
    unittest.main()
