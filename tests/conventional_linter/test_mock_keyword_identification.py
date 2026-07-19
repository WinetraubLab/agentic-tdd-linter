"""Verify mock keyword identification.

Terms:
- `Mock`: Mock identifies the standard mocking utility used by a test. For example, a Mock can supply a controlled dependency result.
- `patch`: Patch identifies temporary replacement of a dependency during a test. For example, patch can substitute a network client.
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
        Conventional linter emits an issue when `Mock` appears without mock details.
        Specialized usage: For mock documentation, mock detail is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        When code invokes `Mock`, _lint_requirement_source contains `mocking_detail_missing`.
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
        Conventional linter emits an issue when `patch` appears without mock details.
        Specialized usage: For patch documentation, mock detail is absent instead of present.

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
        Conventional linter accepts tests when `Mock` descriptions are present.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        When details describe `Mock`, _lint_requirement_source excludes `mocking_detail_missing`.
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
