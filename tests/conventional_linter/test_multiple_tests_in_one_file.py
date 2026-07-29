"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for validating every extracted test independently when a file contains multiple tests.

Terms:
- `JSDoc`: JSDoc is the documentation comment attached to a TypeScript test. For example, a block beginning slash-star-star can contain Requirement Tested.
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

from tests.conventional_linter.test_harness.multiple_tests_in_one_file import (
    _lint_multi_python_source,
    _lint_multi_typescript_source,
)


class MultiTestsInOneFileTests(unittest.TestCase):
    def test_python_multiple_tests_pass(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` validates every extracted test independently when one Python file contains multiple tests.
        Specialized usage: One Python file contains two tests rather than one test.

        Verification Method: verify private function output

        Verification Detail:
        Both tests contain docstrings.
        Both tests contain assertions.
        `_lint_multi_python_source` output contains zero issues.

        Similar Coverage:
        - Higher Level Test: `test_load_all_formats.py::test_loads_python_tests`
          Justification: Deeper coverage — The current test isolates conventional validation for multiple Python tests in one file. The higher test loads Python tests through complete packet generation.
        """

        rules = _lint_multi_python_source(
            """
            def test_collapses_steps() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Report renderer collapses completed prefix steps.

                Verification Method: verify public function output

                Verification Detail:
                Rendered Markdown contains omitted-step marker.
                \"\"\"

                assert "| ... | 2 earlier completed step(s) omitted |" in render_table()


            def test_includes_units() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Report renderer includes both parent units.

                Verification Method: verify public function output

                Verification Detail:
                Rendered title contains both unit names.
                \"\"\"

                assert "Unit Alpha" in render_table()
                assert "Unit Beta" in render_table()
            """
        )

        self.assertEqual(set(), rules)

    def test_typescript_multiple_tests_pass(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` allows multiple tests in one TypeScript file.
        Specialized usage: For TypeScript aggregation, one file contains multiple tests instead of one test.

        Verification Method: verify private function output

        Verification Detail:
        Both tests contain `JSDoc` comments.
        Both tests contain assertions.
        Rules contain zero issues.

        Similar Coverage:
        - Higher Level Test: `test_load_all_formats.py::test_loads_typescript_tests`
          Justification: Deeper coverage — The current test isolates conventional validation for multiple TypeScript tests in one file. The higher test loads TypeScript tests through complete packet generation.
        """

        rules = _lint_multi_typescript_source(
            """
            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * Report renderer collapses completed prefix steps.
             *
             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Rendered Markdown contains omitted-step marker.
            */
            test(
              "trims completed report prefix steps",
              async () => {
                const result = await renderTable(report);

                assert.ok(
                  result.markdown.includes(
                    "| ... | 2 earlier completed step(s) omitted |  |  |"
                  )
                );
              }
            );

            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * Report renderer includes both parent units.
             *
             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Rendered title contains both unit names.
            */
            test(
              "includes both parent units",
              async () => {
                const result = await renderTable(report);

                assert.ok(result.markdown.includes("Unit Alpha"));
                assert.ok(result.markdown.includes("Unit Beta"));
              }
            );
            """
        )

        self.assertEqual(set(), rules)


if __name__ == "__main__":
    unittest.main()
