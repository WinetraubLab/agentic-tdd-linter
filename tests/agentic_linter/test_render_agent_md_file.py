"""Tests in this file validate `render_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/render_agent_md_file.py`.
`render_agent_md_file` is responsible for creating one isolated single-test `.agent.md` with a pending review scorecard.

Terms:
- `single-test packet`: A single-test packet is the `.agent.md` file for one test. For example, it contains one test and its pending review scorecard.
- `iterative review`: Iterative review records original scoring, bounded revision attempts, and final clarity comparison for one packet.
- `Test Content`: Test Content is the packet section containing the original extracted test source. For example, the final scorecard evaluates this source after considering hypothetical revisions.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_tdd_linter.agentic_linter.render_agent_md_file import (
    _render_agent_md_files_for_test_file,
    render_agent_md_file,
)


class AgenticMarkdownTests(unittest.TestCase):
    def test_includes_review_isolation_instructions(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` constrains `single-test packet` review context to the packet itself.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `render_agent_md_file` output contains the instruction `Provide only this Markdown file as the review packet`.
        `render_agent_md_file` output contains the instruction `Do not inspect repository files, manifests, outer unit tests`.

        Similar Coverage:
        - Module Difference: `test_render_cross_test_agent_md_file.py::test_instructions_limit_review_to_packet`
          Explanation: The current test verifies `render_agent_md_file` constrains `single-test packet` review context to the packet itself. The named test verifies `render_cross_test_agent_md_file` constrains `cross-test packet` context to the packet and listed test docstrings; both exercise materially the same scenario through different named modules or contract subjects.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn("Provide only this Markdown file as the review packet", markdown)
        self.assertIn(
            "Do not inspect repository files, manifests, outer unit tests",
            markdown,
        )

    def test_requires_fresh_reviewers(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` requires one fresh isolated reviewer for each `single-test packet`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `render_agent_md_file` output contains `Use one fresh isolated reviewer for this Markdown packet`.

        Similar Coverage:
        - Module Difference: `test_render_cross_test_agent_md_file.py::test_uses_one_reviewer_per_packet`
          Explanation: The current test verifies `render_agent_md_file` requires one fresh isolated reviewer for each `single-test packet`. The named test verifies `render_cross_test_agent_md_file` uses the same fresh isolated reviewer for every pair classification in one `cross-test packet`; both exercise materially the same scenario through different named modules or contract subjects.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn(
            "Use one fresh isolated reviewer for this Markdown packet",
            markdown,
        )

    def test_requires_complete_review(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` requires the reviewer to evaluate every criterion in each `single-test packet`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `render_agent_md_file` output contains `The reviewer shall evaluate every criterion`.

        Similar Coverage:
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_uses_one_reviewer_per_packet`
          Explanation: The current test verifies `render_agent_md_file` requires the reviewer to evaluate every criterion in each `single-test packet`. The named test verifies `render_cross_test_agent_md_file` uses the same fresh isolated reviewer for every pair classification in one `cross-test packet`; both use happy path, but exercise materially different scenarios.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn(
            "The reviewer shall evaluate every criterion",
            markdown,
        )

    def test_iterative_review_records_revision_attempts(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` creates an `iterative review` record with an initial score, three revision slots, and a final assessment.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The `render_agent_md_file` output contains initial, first-revision, second-revision, third-revision, and final-assessment records.

        Similar Coverage:
        - Scenario Difference: `test_render_agent_md_file.py::test_iterative_review_compares_clarity`
          Explanation: The current test verifies `render_agent_md_file` creates an `iterative review` record with an initial score, three revision slots, and a final assessment. The named test verifies `render_agent_md_file` directs `iterative review` to retain original wording and pass the corresponding formulation rows unless a revision removes a materially different interpretation; both use happy path, but exercise materially different scenarios.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn("## Review Iteration Record", markdown)
        self.assertIn("### Initial Score", markdown)
        self.assertIn("### Revision 1", markdown)
        self.assertIn("### Revision 2", markdown)
        self.assertIn("### Revision 3", markdown)
        self.assertIn("### Final Assessment", markdown)

    def test_iterative_review_compares_clarity(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` directs `iterative review` to retain original wording and pass the corresponding formulation rows unless a revision removes a materially different interpretation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The `render_agent_md_file` output defines significant clarity as removing a materially different interpretation.
        The `render_agent_md_file` output excludes shorter wording and grammatical preference from significant clarity.
        The `render_agent_md_file` output directs the reviewer to retain the original and pass the corresponding formulation rows when the revision is not significantly clearer.

        Similar Coverage:
        - Scenario Difference: `test_render_agent_md_file.py::test_iterative_review_records_revision_attempts`
          Explanation: The current test verifies `render_agent_md_file` directs `iterative review` to retain original wording and pass the corresponding formulation rows unless a revision removes a materially different interpretation. The named test verifies `render_agent_md_file` creates an `iterative review` record with an initial score, three revision slots, and a final assessment; both use happy path, but exercise materially different scenarios.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn(
            "`Significantly clearer` means that the original permits a "
            "materially different interpretation",
            markdown,
        )
        self.assertIn(
            "Shorter wording, a grammatical preference",
            markdown,
        )
        self.assertIn(
            "If the revision is about as clear as or less clear than the original",
            markdown,
        )
        self.assertIn(
            "keep the original and pass the corresponding formulation rows",
            markdown,
        )

    def test_iterative_review_scores_original(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` directs the final scorecard to evaluate the original `Test Content`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The rendered instruction assigns final scorecard evaluation to the original `Test Content`.
        The rendered instruction prevents a hypothetical revision from making the original pass.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn(
            "The final scorecard always evaluates the original `Test Content`",
            markdown,
        )
        self.assertIn(
            "A hypothetical revision cannot make the original pass",
            markdown,
        )

    def test_creates_pending_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Filesystem contains `render_agent_md_file` output path.
        File contains the test source supplied to `render_agent_md_file` exactly once.
        File contains 26 pending rows.

        Similar Coverage:
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_deduplicates_cross_test_paths`
          Explanation: The current test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows. The named test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing one docstring entry for every unique selected path; both use happy path, but exercise materially different scenarios.
        - Module Difference: `test_render_cross_test_agent_md_file.py::test_embeds_docstrings_without_test_implementation`
          Explanation: The current test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows. The named test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing each test identifier and docstring without its implementation; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_load_all_formats.py::test_loads_python_tests`
          Explanation: The current test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows. The named test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_load_all_formats.py::test_loads_typescript_tests`
          Explanation: The current test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows. The named test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_refresh_scenario`
          Explanation: The current test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows. The named test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; the current test is happy path, while the named test is failure path.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_directory = root / "tests"
            test_directory.mkdir()
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = test_directory / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")
            test = _render_agent_md_files_for_test_file(test_file, root)[0][0]

            artifact_path = render_agent_md_file(
                test_file_path=test_file,
                test=test,
                repo_root=root,
            )
            artifact_exists = artifact_path.is_file()
            artifact_text = artifact_path.read_text(encoding="utf-8")

        self.assertTrue(artifact_exists)
        self.assertEqual(1, artifact_text.count(source))
        self.assertEqual(26, artifact_text.count("| pending |"))

if __name__ == "__main__":
    unittest.main()
