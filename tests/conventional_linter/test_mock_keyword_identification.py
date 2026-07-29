"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for requiring mock details when test code uses mocking constructs.

Terms:
- `Mock`: Mock identifies the standard mocking utility used by a test. For example, a Mock can supply a controlled dependency result.
- `patch`: Patch identifies temporary replacement of a dependency during a test. For example, patch can substitute a network client.
- `mocking_detail_missing`: This rule identifies a mock without documentation of its role. For example, the rule is omitted when the test explains its Mock.
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

from tests.conventional_linter.test_harness.mock_keyword_identification import (
    _lint_requirement_source,
)


class MockKeywordIdentificationTests(unittest.TestCase):
    def test_mock_call_without_detail_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits `mocking_detail_missing` when test code invokes `Mock` and its documentation omits mock details.
        Specialized usage: When test code invokes `Mock` without documented mock details, `conventional_linter` emits `mocking_detail_missing`.

        Verification Method: verify private function output

        Verification Detail:
        Test code invokes `Mock`.
        The `_lint_requirement_source` output contains `mocking_detail_missing`.
        """

        rules = _lint_requirement_source(
            """
            from unittest.mock import Mock


            def test_fetches_value() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                service produces normalized text.

                Verification Method: verify public function output

                Verification Detail:
                Normalized text equals `ok`.
                \"\"\"

                dependency = Mock(return_value="ok")
                assert dependency() == "ok"
            """
        )

        self.assertIn("mocking_detail_missing", rules)

    def test_patch_decorator_without_detail_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits mocking_detail_missing when `patch` appears without mock details.
        Specialized usage: Test documentation omits mock detail instead of providing it, so conventional linter emits mocking_detail_missing.

        Verification Method: verify private function output

        Verification Detail:
        When code invokes `patch`, _lint_requirement_source contains `mocking_detail_missing`.
        """

        rules = _lint_requirement_source(
            """
            from unittest.mock import patch


            @patch("test_sample.lookup")
            def test_reads_lookup(patched_lookup) -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                lookup produces normalized text.

                Verification Method: verify public function output

                Verification Detail:
                Normalized text equals `ok`.
                \"\"\"

                patched_lookup.return_value = "ok"
                assert patched_lookup() == "ok"
            """
        )

        self.assertIn("mocking_detail_missing", rules)

    def test_mock_detail_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` omits `mocking_detail_missing` when test documentation describes `Mock`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `_lint_requirement_source` output omits `mocking_detail_missing`.
        """

        rules = _lint_requirement_source(
            """
            from unittest.mock import Mock


            def test_fetches_value() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                service produces normalized text.

                Verification Method: verify public function output

                Verification Detail:
                Mocked dependency produces normalized text.
                \"\"\"

                dependency = Mock(return_value="ok")
                assert dependency() == "ok"
            """
        )

        self.assertNotIn("mocking_detail_missing", rules)


if __name__ == "__main__":
    unittest.main()
