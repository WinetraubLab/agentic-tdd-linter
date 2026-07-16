"""Verify test-path and verification-method classification.

Terms:
- `happy path`: Happy path labels a test scenario where parser input succeeds. For example, a parser accepts a supported value on the happy path.
- `failure path`: Failure path labels a test scenario where parser input is rejected. For example, a parser reports malformed syntax on the failure path.
- `edge path`: Edge path labels a test scenario outside the supported classifications. For example, the linter rejects edge path as an invalid Test Path value.
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

from tests.conventional_linter.classification import (
    _lint_classification_source,
)


class ClassificationTests(unittest.TestCase):
    def test_accepts_happy_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The linter accepts `happy path` when parser input succeeds.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        When paths equal `happy path`, rules contain zero issues.
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
        The linter accepts `failure path` when parser input fails.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        When paths equal `failure path`, rules contain zero issues.
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

