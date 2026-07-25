"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for validating test-path and verification-method classifications.

Terms:
- `happy path`: Happy path labels a test scenario where parser input succeeds. For example, a parser accepts a supported value on the happy path.
- `failure path`: Failure path labels a test scenario where parser input is rejected. For example, a parser reports malformed syntax on the failure path.
- `supported methods`: Supported methods are public function output, private function output, and visual inspection by user. For example, conventional linter accepts public function output.
- `invalid_verification_method`: This rule identifies a Verification Method value outside supported methods. For example, verify database state produces invalid_verification_method.
- `visual inspection contract`: A visual inspection contract requires `visual inspection by user`, an artifact path, inspection instructions, and an artifact-writing helper call. For example, a rendering test documents an image path and inspection steps and invokes `write_visual_inspection_artifact`.
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

from tests.conventional_linter.test_harness.classification import (
    _lint_classification_source,
)


class ClassificationTests(unittest.TestCase):
    def test_accepts_happy_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts `happy path` when parser input succeeds.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        When paths correspond to `happy path`, rules contain zero issues.
        """

        rules = _lint_classification_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Addition produces totals.

                Verification Method: verify public function output

                Verification Detail:
                The sum equals two.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertEqual(set(), rules)

    def test_accepts_failure_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts `failure path`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        When paths correspond to `failure path`, validator rules contain zero issues.
        """

        rules = _lint_classification_source(
            """
            def test_rejects_value() -> None:
                \"\"\"Test Path: failure path

                Requirement Tested:
                Validation prohibits text.

                Verification Method: verify public function output

                Verification Detail:
                The result contains an error.
                \"\"\"

                assert validate("") == "error"
            """
        )

        self.assertEqual(set(), rules)

    def test_accepts_public_output(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts public function output when tests observe public function output.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Public functions produce public-function output.
        Rules contain zero issues.
        """

        rules = _lint_classification_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Addition produces totals.

                Verification Method: verify public function output

                Verification Detail:
                The sum equals two.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertEqual(set(), rules)

    def test_accepts_private_output(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts private function output when tests observe private function output.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Private helpers produce private-helper output.
        Rules contain zero issues.
        """

        rules = _lint_classification_source(
            """
            def _add_values(left: int, right: int) -> int:
                return left + right


            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Addition produces totals.

                Verification Method: verify private function output

                Verification Detail:
                _add_values produces two.
                \"\"\"

                assert _add_values(1, 1) == 2
            """
        )

        self.assertEqual(set(), rules)

    def test_accepts_visual_inspection(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts a `visual inspection contract`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `conventional_linter` output contains zero issues.
        The test docstring declares `visual inspection by user`.
        The test docstring contains `tests/artifacts/addition.png`.
        The test docstring contains inspection instructions.
        The test source invokes `write_visual_inspection_artifact`.
        """

        rules = _lint_classification_source(
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

                write_visual_inspection_artifact()
            """
        )

        self.assertEqual(set(), rules)

    def test_rejects_unsupported_verification_method(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` accepts only `supported methods` as Verification Method values.
        Specialized usage: The test declares "verify database state" instead of a supported method, so conventional linter emits `invalid_verification_method`.

        Verification Method: verify private function output

        Verification Detail:
        `_lint_classification_source` output contains `invalid_verification_method` for `Verification Method: verify database state`.
        """

        rules = _lint_classification_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify database state

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_method", rules)


if __name__ == "__main__":
    unittest.main()
