"""Tests in this file validate `determine_agent_md_status` located at `src/agentic_tdd_linter/agentic_linter/determine_agent_md_status.py`.
`determine_agent_md_status` is responsible for deriving one status from the review results in a `.agent.md` scorecard.
"""

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
    def test_derives_pass_status(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `determine_agent_md_status` derives pass status when every scorecard row succeeds.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        `determine_agent_md_status` produces `pass`.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Justification: Deeper coverage — The current test isolates pass-status derivation. The higher test combines passing and failing scorecards through the complete CLI workflow.
        """

        artifact = """# Agentic Test Review

## Review Scorecard

| # | Criterion | Result | Notes |
|---:|---|---|---|
| 1 | Criterion 1 | pass | Review evidence. |
| 2 | Criterion 2 | pass | Review evidence. |
"""

        status = determine_agent_md_status(artifact)

        self.assertEqual("pass", status)

    def test_derives_fail_status(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `determine_agent_md_status` derives fail status when any scorecard row has fail status.
        Specialized usage: One row has fail status instead of pass status, so agentic linter derives fail status.

        Verification Method: verify public function output

        Verification Detail:
        `determine_agent_md_status` produces `fail`.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Justification: Deeper coverage — The current test isolates fail-status precedence. Higher test verifies failed-review guidance through the complete CLI workflow.
        """

        artifact = """# Agentic Test Review

## Review Scorecard

| # | Criterion | Result | Notes |
|---:|---|---|---|
| 1 | Criterion 1 | pass | Review evidence. |
| 2 | Criterion 2 | fail | Review evidence. |
"""

        status = determine_agent_md_status(artifact)

        self.assertEqual("fail", status)

    def test_derives_pending_status(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows.
        Specialized usage: Scorecard contains a pending row alongside a passing row instead of only passing rows, so agentic linter derives pending status.

        Verification Method: verify public function output

        Verification Detail:
        `determine_agent_md_status` produces `pending`.
        """

        artifact = """# Agentic Test Review

## Review Scorecard

| # | Criterion | Result | Notes |
|---:|---|---|---|
| 1 | Criterion 1 | pass | Review evidence. |
| 2 | Criterion 2 | pending | Review evidence. |
"""

        status = determine_agent_md_status(artifact)

        self.assertEqual("pending", status)

    def test_rejects_ambiguous_row_result(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `determine_agent_md_status` emits invalid_review_scorecard when criteria contain multiple results.
        Specialized usage: One criterion contains pass/fail ambiguity instead of one result, so agentic linter emits invalid_review_scorecard.

        Verification Method: verify private function output

        Verification Detail:
        Rules contain `invalid_review_scorecard`.
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
