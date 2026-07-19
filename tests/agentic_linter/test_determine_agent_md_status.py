"""Verify `.agent.md` scorecard status determination."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_tdd_linter.agentic_linter.determine_agent_md_status import (
    _lint_agent_md_file,
    determine_agent_md_status,
)
from agentic_tdd_linter.agentic_linter.render_agent_md_file import (
    _write_agent_md_files_for_test_file,
)


class AgentMdStatusTests(unittest.TestCase):
    def test_derives_scorecard_status(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agentic linter treats a review as passing only when every scorecard criterion passes.
        A review fails when any completed criterion fails and remains pending while any criterion is incomplete.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Two passing rows produce `pass`.
        One failed row produces `fail`.
        One pending row produces `pending`.
        """

        cases = (
            (("pass", "pass"), "pass"),
            (("pass", "fail"), "fail"),
            (("pass", "pending"), "pending"),
        )

        for results, expected_status in cases:
            with self.subTest(results=results):
                rows = "\n".join(
                    f"| {number} | Criterion {number} | {result} | Review evidence. |"
                    for number, result in enumerate(results, start=1)
                )
                artifact = f"""# Agentic Test Review

## Review Scorecard

| # | Criterion | Result | Notes |
|---:|---|---|---|
{rows}
"""

                status = determine_agent_md_status(artifact)

                self.assertEqual(expected_status, status)

    def test_rejects_multiple_results_in_one_row(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic linter rejects ambiguous review evidence because every scorecard criterion must contain exactly one result.
        Specialized usage: One criterion contains `pass/fail` instead of one result.

        Verification Method: verify private function output

        Verification Detail:
        The issue rules contain `invalid_review_scorecard`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_sample.py"
            test_file.parent.mkdir()
            test_file.write_text(
                'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n',
                encoding="utf-8",
            )
            artifact_path = _write_agent_md_files_for_test_file(test_file, root)[0]
            artifact_text = artifact_path.read_text(encoding="utf-8")
            artifact_text = artifact_text.replace("| pending |", "| pass |")
            artifact_text = artifact_text.replace("| pass |", "| pass/fail |", 1)
            artifact_path.write_text(artifact_text, encoding="utf-8")

            issues = _lint_agent_md_file(
                test_file,
                repo_root=root,
                test_name="test_adds_values",
            )

        self.assertIn("invalid_review_scorecard", {issue.rule for issue in issues})


if __name__ == "__main__":
    unittest.main()
