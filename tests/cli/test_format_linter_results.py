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
        `format_text` renders issues.
        When the linter finds one issue, `format_text` renders it.

        Verification Method: verify public function output

        Verification Detail:
        `format_text` output contains `sample_rule`.
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

    def test_formats_json_report(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `format_json` renders summaries.
        When the linter finds zero issues for one file, `format_json` renders the summary.

        Verification Method: verify public function output

        Verification Detail:
        `format_json` output contains `PASS`.
        `format_json` output contains one checked file.
        """

        output = format_json([], [Path("tests/test_sample.py")])

        payload = json.loads(output)
        self.assertEqual("PASS", payload["status"])
        self.assertEqual(1, payload["files_checked"])


if __name__ == "__main__":
    unittest.main()
