"""Verify test-path and verification-method classification.

Terms:
- `happy path`: Happy path labels a test scenario where parser input succeeds. For example, a parser accepts a supported value on the happy path.
- `failure path`: Failure path labels a test scenario where parser input is rejected. For example, a parser reports malformed syntax on the failure path.
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
        Conventional linter accepts `happy path` when parser input succeeds.
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
        Conventional linter accepts `failure path`.
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
        Conventional linter accepts public verification when tests observe public-function output.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Public functions produce the output.
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
        Conventional linter accepts private verification when tests observe private-helper output.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Private helpers produce the output.
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
        Conventional linter accepts visual inspection when tests emit review artifacts.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        When methods name inspection, rules contain zero issues.
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
        Conventional linter reports an invalid-verification-method issue unless Verification Method is public function output, private function output, or visual inspection by user.
        Specialized usage: The test declares "verify database state", which is not a supported Verification Method value.

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
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_method", rules)


if __name__ == "__main__":
    unittest.main()
