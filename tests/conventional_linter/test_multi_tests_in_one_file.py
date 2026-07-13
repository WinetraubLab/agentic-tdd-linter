from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_tdd_linter.docstrings import lint_test_files


class MultiTestsInOneFileTests(unittest.TestCase):
    def test_python_multiple_tests_pass(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Python test files contain multiple tests.
        Linter evaluates each Python test function individually.

        Verification Method: verify public function output

        Verification Detail:
        Rule set is empty when both Python tests include docstrings and assertions.
        """

        rules = _lint_source(
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
        `test.ts` files contain multiple tests.
        Linter evaluates each JSDoc-backed TypeScript test individually.

        Verification Method: verify public function output

        Verification Detail:
        Rule set is empty when both TypeScript tests include JSDoc and assertions.
        """

        rules = _lint_typescript_source(
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
              "presents a report with ten steps and trims completed prefix steps",
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
              "presents an activity with two parent units",
              async () => {
                const result = await renderTable(report);

                assert.ok(result.markdown.includes("Unit Alpha"));
                assert.ok(result.markdown.includes("Unit Beta"));
              }
            );
            """
        )

        self.assertEqual(set(), rules)


def _lint_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


def _lint_typescript_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_directory = repo_root / "tests"
        test_directory.mkdir()
        test_file = test_directory / "localArtifactRoundTrip.test.ts"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


if __name__ == "__main__":
    unittest.main()
