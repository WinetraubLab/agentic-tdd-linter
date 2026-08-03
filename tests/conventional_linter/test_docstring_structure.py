"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for enforcing test documentation, naming, and visual-inspection conventions.

Terms:
- `Test Path`: Test Path is the structured field naming a test's scenario category. For example, Test Path can contain happy path.
- `Requirement Tested`: Requirement Tested is the structured field stating behavior and scenario. For example, it says that a parser accepts valid text.
- `Verification Method`: Verification Method is the structured field naming the observation approach. For example, it can say verify public function output.
- `Verification Detail`: Verification Detail is the structured field stating exact evidence. For example, it says that `_add_values` output equals three.
- `Inspection Instructions`: Inspection Instructions is the structured field that authorizes source inspection when linter issues cannot describe visual evidence. For example, it can name a specific module to inspect.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentic_tdd_linter.conventional_linter.run_conventional_linter import (
    run_conventional_linter,
)
from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)

from tests.conventional_linter.test_harness.docstring_structure import (
    _lint_docstring_source,
    _lint_typescript_docstring_source,
)


class DocstringStructureTests(unittest.TestCase):
    def test_reports_missing_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_docstring when a test lacks a test docstring.
        Specialized usage: The extracted record contains an empty test docstring instead of a populated docstring, so conventional linter emits missing_docstring.

        Verification Method: verify public function output

        Verification Detail:
        `conventional_linter` output contains `missing_docstring`.
        """

        test = ExtractedTestRecord(
            path=Path("tests/test_sample.py"),
            name="test_sample",
            line=1,
            node=None,
            docstring="",
            source="def test_sample(): pass",
        )
        rules = {issue.rule for issue in run_conventional_linter(test)}

        self.assertIn("missing_docstring", rules)

    def test_reports_missing_test_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`.
        Specialized usage: When a test docstring omits `Test Path`, `conventional_linter` emits missing_test_path.

        Verification Method: verify private function output

        Verification Detail:
        The `_lint_docstring_source` rules contain `missing_test_path`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"
                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_test_path", rules)

    def test_reports_empty_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing.
        Specialized usage: When a docstring contains empty `Requirement Tested`, `conventional_linter` emits missing_requirement.

        Verification Method: verify private function output

        Verification Detail:
        When `Requirement Tested` contains nothing, `_lint_docstring_source` output contains `missing_requirement`.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_classic_linter_errors_scenario`
          Justification: Diagnostic completeness — The current test proves the exact missing-requirement rule. The higher test proves that a conventionally invalid test prevents packet creation.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_requirement", rules)

    def test_reports_missing_method(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`.
        Specialized usage: Docstring omits `Verification Method` instead of providing it, so `conventional_linter` emits missing_verification_method.

        Verification Method: verify private function output

        Verification Detail:
        When docstrings omit `Verification Method`, _lint_docstring_source contains `missing_verification_method`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_verification_method", rules)

    def test_reports_empty_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing.
        Specialized usage: When a docstring has an empty `Verification Detail`, `conventional_linter` emits missing_verification_detail.

        Verification Method: verify private function output

        Verification Detail:
        When `Verification Detail` contains nothing, `_lint_docstring_source` output contains `missing_verification_detail`.
        """

        rules = _lint_docstring_source(
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
        `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection.
        Specialized usage: When `Verification Detail` lacks an image path for visual inspection, `conventional_linter` emits missing_visual_inspection_artifact.

        Verification Method: verify private function output

        Verification Detail:
        `_lint_docstring_source` output contains `missing_visual_inspection_artifact`.

        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes an image for review.

                Inspection Instructions:
                Confirm the image shows the expected addition result.
                \"\"\"

                write_visual_inspection_artifact()
            """
        )

        self.assertIn("missing_visual_inspection_artifact", rules)

    def test_reports_missing_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`.
        Specialized usage: The fixture docstring declares visual inspection by user in its `Verification Method` but omits `Inspection Instructions`, so `conventional_linter` emits missing_inspection_instructions.

        Verification Method: verify private function output

        Verification Detail:
        When the fixture docstring declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`, `_lint_docstring_source` output contains `missing_inspection_instructions`.

        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes tests/artifacts/addition.png.
                \"\"\"

                write_visual_inspection_artifact()
            """
        )

        self.assertIn("missing_inspection_instructions", rules)

    def test_reports_missing_visual_helper(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact.
        Specialized usage: When a test declares visual inspection by user but lacks a write_visual_inspection_artifact call, `conventional_linter` emits missing_visual_inspection_helper.

        Verification Method: verify private function output

        Verification Detail:
        When a test declares visual inspection by user but omits a `write_visual_inspection_artifact` call, `_lint_docstring_source` output contains `missing_visual_inspection_helper`.

        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes tests/artifacts/addition.png.

                Inspection Instructions:
                Confirm the image shows the expected addition result.
                \"\"\"

                pass
            """
        )

        self.assertIn("missing_visual_inspection_helper", rules)

    def test_reports_long_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` prohibits test names when they exceed five words.
        Specialized usage: For Python naming, a test name exceeds five words instead of staying within five, so `conventional_linter` emits test_name_too_long.

        Verification Method: verify private function output

        Verification Detail:
        Conventional linter enforces a five-word limit.
        When names contain seven words, _lint_docstring_source contains `test_name_too_long`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_two_positive_integer_values_correctly() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("test_name_too_long", rules)

    def test_reports_long_typescript_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` prohibits TypeScript labels when they exceed five words.
        Specialized usage: For TypeScript naming, test label exceeds five words instead of staying within five, so conventional linter emits test_name_too_long.

        Verification Method: verify private function output

        Verification Detail:
        Conventional linter enforces a five-word limit.
        When labels contain six words, _lint_typescript_docstring_source contains `test_name_too_long`.
        """

        rules = _lint_typescript_docstring_source(
            """
            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * Addition returns the expected sum.
             * This rule applies to positive integers.
             *
             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Addition output equals two.
             */
            test("adds two positive integer values correctly", () => {
              assert.equal(1 + 1, 2);
            });
            """
        )

        self.assertIn("test_name_too_long", rules)

    def test_reports_same_line_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline.
        Specialized usage: Docstring locates `Requirement Tested` inline instead of on a separate line, so conventional linter emits invalid_requirement_format.

        Verification Method: verify private function output

        Verification Detail:
        When requirement text remains inline, _lint_docstring_source contains `invalid_requirement_format`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested: addition returns the expected sum.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_requirement_format", rules)

    def test_reports_same_line_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline.
        Specialized usage: Docstring locates `Verification Detail` inline instead of on a separate line, so conventional linter emits invalid_verification_detail_format.

        Verification Method: verify private function output

        Verification Detail:
        When detail text remains inline, _lint_docstring_source contains `invalid_verification_detail_format`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail: Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_detail_format", rules)

    def test_reports_same_line_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline.
        Specialized usage: Docstring locates `Inspection Instructions` inline instead of on a separate line, so conventional linter emits invalid_inspection_instructions_format.

        Verification Method: verify private function output

        Verification Detail:
        When instructions stay inline, _lint_docstring_source contains `invalid_inspection_instructions_format`.
        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes tests/artifacts/addition.png.

                Inspection Instructions: Confirm the image shows the expected addition result.
                \"\"\"

                write_visual_inspection_artifact()
            """
        )

        self.assertIn("invalid_inspection_instructions_format", rules)

    def test_typescript_fields_need_blank_lines(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent.
        Specialized usage: TypeScript doc comment locates metadata fields adjacent instead of separating them with blank lines, so conventional linter emits invalid_field_spacing.

        Verification Method: verify private function output

        Verification Detail:
        Rule set contains `invalid_field_spacing`.
        """

        rules = _lint_typescript_docstring_source(
            """
            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             * Requirement Tested:
             * Local artifact writes survive a primitive round trip.
             * Verification Method: verify public function output
             * Verification Detail:
             * Loaded artifact content equals written artifact content.
             */
            test("local artifact round trip", () => {
              assert.equal(readLocalArtifact(), "saved artifact");
            });
            """
        )

        self.assertIn("invalid_field_spacing", rules)

    def test_python_docstring_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The docstring contains four fields.
        The test contains `Test Path`.
        The test contains `Requirement Tested`.
        The test contains `Verification Method`.
        The test contains `Verification Detail`.
        The `_lint_docstring_source` output rules contain zero issues.

        Similar Coverage:
        - Lower Level Test: `test_classification.py::test_accepts_happy_path`
          Justification: Diagnostic completeness — The lower test isolates whether `happy path` alone is accepted. The current test combines that classification with three other required Python docstring fields.
        - Lower Level Test: `test_classification.py::test_accepts_public_output`
          Justification: Diagnostic completeness — The lower test isolates whether public function output alone is accepted. The current test combines that method with three other required Python docstring fields.
        - Higher Level Test: `test_load_all_formats.py::test_loads_python_tests`
          Justification: Deeper coverage — The current test directly validates every required Python docstring field. The higher test loads that documentation into complete Python packets without isolating conventional docstring validation.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected sum.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertEqual(set(), rules)

    def test_typescript_doc_comment_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `JSDoc` contains four fields.
        The test contains `Test Path`.
        The test contains `Requirement Tested`.
        The test contains `Verification Method`.
        The test contains `Verification Detail`.
        Rules contain zero issues.

        Similar Coverage:
        - Lower Level Test: `test_classification.py::test_accepts_happy_path`
          Justification: Diagnostic completeness — The lower test isolates whether `happy path` alone is accepted. The current test combines that classification with three other required TypeScript docstring fields.
        - Lower Level Test: `test_classification.py::test_accepts_public_output`
          Justification: Diagnostic completeness — The lower test isolates whether public function output alone is accepted. The current test combines that method with three other required TypeScript docstring fields.
        - Higher Level Test: `test_load_all_formats.py::test_loads_typescript_tests`
          Justification: Deeper coverage — The current test directly validates every required TypeScript JSDoc field. The higher test loads that documentation into complete TypeScript packets without isolating conventional docstring validation.
        """

        rules = _lint_typescript_docstring_source(
            """
            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * Local artifact writes survive a primitive round trip.
             *
             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Loaded artifact content equals written artifact content.
             */
            test("local artifact round trip", () => {
              assert.equal(readLocalArtifact(), "saved artifact");
            });
            """
        )

        self.assertEqual(set(), rules)


if __name__ == "__main__":
    unittest.main()
