"""Verify structured test-docstring rules.

Terms:
- `Test Path`: Test Path is the structured field naming a test's scenario category. For example, Test Path can contain happy path.
- `Requirement Tested`: Requirement Tested is the structured field stating behavior and scenario. For example, it says that a parser accepts valid text.
- `Verification Method`: Verification Method is the structured field naming the observation approach. For example, it can say verify public function output.
- `Verification Detail`: Verification Detail is the structured field stating exact evidence. For example, it says that the result equals three.
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
        Conventional linter emits issue when a test has no docstring.
        Specialized usage: For test documentation, test docstring is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        When tests have no docstrings, _lint_docstring_source contains `missing_docstring`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_docstring", rules)

    def test_reports_missing_test_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Conventional linter emits issues when docstrings omit `Test Path`.
        Specialized usage: For path metadata, `Test Path` is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        When docstrings omit `Test Path`, _lint_docstring_source contains `missing_test_path`.
        """

        rules = _lint_docstring_source(
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
        Conventional linter emits issues when `Requirement Tested` contains nothing.
        Specialized usage: For requirement validation, `Requirement Tested` is empty instead of populated.

        Verification Method: verify private function output

        Verification Detail:
        When `Requirement Tested` contains nothing, _lint_docstring_source contains `missing_requirement`.

        Similar Coverage:
        - Higher Level Test: `test_main.py::test_invalid_fixture_exits_one`
          Justification: Diagnostic completeness — This test proves `missing_requirement`. CLI output aggregates the rule.
        """

        rules = _lint_docstring_source(
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
        Conventional linter emits issues when docstrings omit `Verification Method`.
        Specialized usage: For verification metadata, `Verification Method` is absent instead of present.

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
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_verification_method", rules)

    def test_reports_empty_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Conventional linter emits issues when `Verification Detail` contains nothing.
        Specialized usage: For evidence validation, `Verification Detail` is empty instead of populated.

        Verification Method: verify private function output

        Verification Detail:
        When `Verification Detail` contains nothing, _lint_docstring_source contains `missing_verification_detail`.
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
        Conventional linter emits issues when `Verification Detail` omits image paths.
        Specialized usage: For visual evidence, image path is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        When details omit image paths, _lint_docstring_source contains `missing_visual_inspection_artifact`.
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
        Conventional linter emits issues when visual tests omit `Inspection Instructions`.
        Specialized usage: For visual evidence, `Inspection Instructions` is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        When tests omit `Inspection Instructions`, _lint_docstring_source contains `missing_inspection_instructions`.
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
        Conventional linter emits diagnostics when visual tests omit helper calls.
        Specialized usage: For visual evidence, helper call is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        When tests omit `write_visual_inspection_artifact`, _lint_docstring_source contains `missing_visual_inspection_helper`.
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
        Conventional linter prohibits Python names when they exceed five words.
        Specialized usage: For Python naming, test name exceeds five words instead of staying within five.

        Verification Method: verify private function output

        Verification Detail:
        The limit is five words.
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
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("test_name_too_long", rules)

    def test_reports_long_typescript_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Conventional linter prohibits TypeScript labels when they exceed five words.
        Specialized usage: For TypeScript naming, test label exceeds five words instead of staying within five.

        Verification Method: verify private function output

        Verification Detail:
        The limit is five words.
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
             * The returned total equals two.
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
        Conventional linter emits issues when docstrings locate `Requirement Tested` inline.
        Specialized usage: For section layout, `Requirement Tested` is inline instead of on the following line.

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
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_requirement_format", rules)

    def test_reports_same_line_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Conventional linter prohibits the format when docstrings locate `Verification Detail` inline.
        Specialized usage: For section layout, `Verification Detail` is inline instead of on the following line.

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

                Verification Detail: by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_detail_format", rules)

    def test_reports_same_line_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Conventional linter emits issues when docstrings locate `Inspection Instructions` inline.
        Specialized usage: For section layout, `Inspection Instructions` is inline instead of on the following line.

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
        Conventional linter emits issues when TypeScript fields are adjacent.
        Specialized usage: For TypeScript layout, metadata fields are adjacent instead of separated by blank lines.

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
        Conventional linter accepts docstrings when their schema is complete.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The docstring contains four fields.
        The test contains `Test Path`.
        The test contains `Requirement Tested`.
        The test contains `Verification Method`.
        The test contains `Verification Detail`.
        Rules contain zero issues.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Returned total equals expected sum.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertEqual(set(), rules)

    def test_typescript_doc_comment_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Conventional linter accepts comments when their schema is complete.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `JSDoc` contains four fields.
        The test contains `Test Path`.
        The test contains `Requirement Tested`.
        The test contains `Verification Method`.
        The test contains `Verification Detail`.
        Rules contain zero issues.
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
