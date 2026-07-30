"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for validating evidence declared as private-function output."""

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

from tests.conventional_linter.test_harness.private_function_verification import (
    _lint_private_verification_source,
)


class PrivateFunctionVerificationTests(unittest.TestCase):
    def test_private_verification_without_private_call(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits private_verification_missing_private_call when a test declares private-function output but invokes only public helpers.
        Specialized usage: For private-function output, test invokes helper instead of private function, so conventional linter emits private_verification_missing_private_call.

        Verification Method: verify private function output

        Verification Detail:
        The fixture declares `verify private function output`.
        The fixture invokes `helper(" value ")`.
        The lint result contains `private_verification_missing_private_call` because `helper` lacks a leading underscore.
        """

        rules = _lint_private_verification_source(
            """
            def helper(value: str) -> str:
                return value.strip()


            def test_strips_value() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                helper returns text without surrounding whitespace.

                Verification Method: verify private function output

                Verification Detail:
                Helper output equals expected stripped string.
                \"\"\"

                assert helper(" value ") == "value"
            """
        )

        self.assertIn("private_verification_missing_private_call", rules)


if __name__ == "__main__":
    unittest.main()
