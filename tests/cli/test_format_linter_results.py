"""Verify formatting of linter results.

Terms:
- `formatted result`: A formatted result is a text or JSON representation of one lint finding. For example, it names the finding's rule and file path.
- `format_text`: This formatter renders lint findings as human-readable lines. For example, it includes a rule and message in terminal output.
- `format_json`: This formatter renders lint findings as JSON. For example, it produces a JSON array containing the finding rule.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentic_tdd_linter.cli.format_linter_results import format_json, format_text
from agentic_tdd_linter.conventional_linter.run_conventional_linter import LintIssue


class LinterResultFormattingTests(unittest.TestCase):
    def test_formats_text_report(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_text` creates `formatted result` with rule/message pairs.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        `format_text` output contains `Rule: sample_rule`.
        `format_text` output contains `sample message`.
        """

        issue = LintIssue(
            path=Path("tests/test_sample.py"),
            test_name="test_sample",
            line=3,
            rule="sample_rule",
            message="sample message",
        )

        output = format_text([issue], [issue.path])

        self.assertIn("Rule: sample_rule", output)
        self.assertIn("sample message", output)

    def test_formats_json_status(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_json` emits success status.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        `format_json` output contains `PASS`.
        """

        output = format_json([], [Path("tests/test_sample.py")])

        payload = json.loads(output)
        self.assertEqual("PASS", payload["status"])

    def test_formats_json_file_count(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_json` emits checked-file totals.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The summary contains one file.
        """

        output = format_json([], [Path("tests/test_sample.py")])

        payload = json.loads(output)
        self.assertEqual(1, payload["files_checked"])


if __name__ == "__main__":
    unittest.main()
