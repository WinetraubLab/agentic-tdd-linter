"""Tests in this file validate `format_linter_results` located at `src/agentic_tdd_linter/cli/format_linter_results.py`.
`format_linter_results` is responsible for rendering lint findings as terminal text or JSON.

Terms:
- `formatted result`: A formatted result is output owned by a CLI formatter for one lint finding. For example, CLI formatter output names the finding's rule and file path.
- `format_text`: This formatter renders lint findings as human-readable lines. For example, it includes a rule and message in terminal output.
- `format_json`: This formatter renders lint findings as JSON. For example, it produces a JSON array containing the finding rule.
- `PASS`: PASS is the JSON status for lint output with zero issues. For example, format_json emits PASS for an empty issue list.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentic_tdd_linter.cli import format_linter_results
from agentic_tdd_linter.conventional_linter.run_conventional_linter import LintIssue


class LinterResultFormattingTests(unittest.TestCase):
    def test_formats_text_report(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_linter_results` creates a human-readable `formatted result` containing each lint finding's rule and message.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        `formatted result` contains `Rule: sample_rule`.
        `formatted result` contains `sample message`.

        Similar Coverage:
        - Scenario Difference: `test_format_linter_results.py::test_formats_json_file_count`
          Explanation: The current test verifies `format_linter_results` creates a human-readable `formatted result` containing each lint finding's rule and message. The named test verifies `format_linter_results` emits `format_json` field files_checked equal to the checked-path count; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_format_linter_results.py::test_formats_json_status`
          Explanation: The current test verifies `format_linter_results` creates a human-readable `formatted result` containing each lint finding's rule and message. The named test verifies `format_linter_results` emits JSON status `PASS` when lint has zero issues; both use happy path, but exercise materially different scenarios.
        """

        issue = LintIssue(
            path=Path("tests/test_sample.py"),
            test_name="test_sample",
            line=3,
            rule="sample_rule",
            message="sample message",
        )

        output = format_linter_results.format_text([issue], [issue.path])

        self.assertIn("Rule: sample_rule", output)
        self.assertIn("sample message", output)

    def test_formats_json_status(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_linter_results` emits JSON status `PASS` when it formats zero lint findings.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        JSON `status` field contains exactly `PASS`.

        Similar Coverage:
        - Scenario Difference: `test_format_linter_results.py::test_formats_json_file_count`
          Explanation: The current test verifies `format_linter_results` emits JSON status `PASS` when lint has zero issues. The named test verifies `format_linter_results` emits `format_json` field files_checked equal to the checked-path count; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_format_linter_results.py::test_formats_text_report`
          Explanation: The current test verifies `format_linter_results` emits JSON status `PASS` when lint has zero issues. The named test verifies `format_linter_results` creates a human-readable `formatted result` containing each lint finding's rule and message; both use happy path, but exercise materially different scenarios.
        """

        output = format_linter_results.format_json(
            [],
            [Path("tests/test_sample.py")],
        )

        payload = json.loads(output)
        self.assertEqual("PASS", payload["status"])

    def test_formats_json_file_count(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_linter_results` emits `format_json` field files_checked equal to the checked-path count.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        JSON `files_checked` field contains exactly `1`.

        Similar Coverage:
        - Scenario Difference: `test_format_linter_results.py::test_formats_json_status`
          Explanation: The current test verifies `format_linter_results` emits `format_json` field files_checked equal to the checked-path count. The named test verifies `format_linter_results` emits JSON status `PASS` when lint has zero issues; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_format_linter_results.py::test_formats_text_report`
          Explanation: The current test verifies `format_linter_results` emits `format_json` field files_checked equal to the checked-path count. The named test verifies `format_linter_results` creates a human-readable `formatted result` containing each lint finding's rule and message; both use happy path, but exercise materially different scenarios.
        """

        output = format_linter_results.format_json(
            [],
            [Path("tests/test_sample.py")],
        )

        payload = json.loads(output)
        self.assertEqual(1, payload["files_checked"])


if __name__ == "__main__":
    unittest.main()
