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
