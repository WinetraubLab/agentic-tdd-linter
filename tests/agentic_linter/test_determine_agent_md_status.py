"""Tests in this file validate `determine_agent_md_status` located at `src/agentic_tdd_linter/agentic_linter/determine_agent_md_status.py`.
`determine_agent_md_status` is responsible for deriving review status and reporting malformed `.agent.md` scorecards.

Terms:
- `.agent.md`: An .agent.md file contains one agent-review scorecard. For example, each criterion row has one review result.
- `invalid_review_scorecard`: invalid_review_scorecard identifies a malformed agent-review scorecard. For example, one result cell containing both pass and fail is invalid.
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
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_derives_fail_status`
          Explanation: The current test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds. The named test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_derives_pending_status`
          Explanation: The current test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds. The named test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_rejects_ambiguous_row_result`
          Explanation: The current test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds. The named test verifies `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Explanation: The current test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds. The named test verifies `pre-commit review workflow` requires editors to consider every scorecard criterion, including passed criteria, before fixing a test with a failed `.agent.md` review; the current test is happy path, while the named test is failure path.
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
        `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status.
        Specialized usage: When an `.agent.md` has one pass result and one fail result, `determine_agent_md_status` derives fail status.

        Verification Method: verify public function output

        Verification Detail:
        The `.agent.md` has one `pass` result and one `fail` result.
        `determine_agent_md_status` produces `fail`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_derives_pass_status`
          Explanation: The current test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status. The named test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_determine_agent_md_status.py::test_derives_pending_status`
          Explanation: The current test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status. The named test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_determine_agent_md_status.py::test_rejects_ambiguous_row_result`
          Explanation: The current test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status. The named test verifies `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Explanation: The current test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status. The named test verifies `pre-commit review workflow` requires editors to consider every scorecard criterion, including passed criteria, before fixing a test with a failed `.agent.md` review; both use failure path, but exercise materially different scenarios.
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

        Similar Coverage:
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_pending_review_is_not_recorded`
          Explanation: The current test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows. The named test verifies `build_manifest_from_agent_md_files` creates `manifest proof` only after the reviewer completes every scorecard row; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_determine_agent_md_status.py::test_derives_fail_status`
          Explanation: The current test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows. The named test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_derives_pass_status`
          Explanation: The current test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows. The named test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_determine_agent_md_status.py::test_rejects_ambiguous_row_result`
          Explanation: The current test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows. The named test verifies `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results; both use failure path, but exercise materially different scenarios.
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
        `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results.
        Specialized usage: When one result cell contains both pass and fail instead of one result, `determine_agent_md_status` emits `invalid_review_scorecard`.

        Verification Method: verify private function output

        Verification Detail:
        One scorecard result cell contains `pass/fail`.
        The module's `_lint_agent_md_file` output contains `invalid_review_scorecard`.

        Similar Coverage:
        - Scenario Difference: `test_determine_agent_md_status.py::test_derives_fail_status`
          Explanation: The current test verifies `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results. The named test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_derives_pass_status`
          Explanation: The current test verifies `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results. The named test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_determine_agent_md_status.py::test_derives_pending_status`
          Explanation: The current test verifies `determine_agent_md_status` emits `invalid_review_scorecard` when one `.agent.md` scorecard row contains both pass and fail results. The named test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows; both use failure path, but exercise materially different scenarios.
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
