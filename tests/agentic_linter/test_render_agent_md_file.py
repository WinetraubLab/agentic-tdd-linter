"""Tests in this file validate `render_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/render_agent_md_file.py`.
`render_agent_md_file` is responsible for creating one isolated single-test `.agent.md` with a pending review scorecard.

Terms:
- `single-test packet`: A single-test packet is the `.agent.md` file for one test. For example, it contains one test and its pending review scorecard.
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
        - Higher Level Test: `test_render_cross_test_agent_md_file.py::test_instructions_limit_review_to_packet`
          Justification: Comparable coverage — The current test constrains single-test review context. The higher test applies the same isolation policy to cross-test review context.
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
        `render_agent_md_file` requires a fresh subagent for every `single-test packet` criterion.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `render_agent_md_file` output contains `Evaluate each criterion in a fresh subagent`.
        """

        with tempfile.TemporaryDirectory() as directory:
            source = 'def test_adds_values() -> None:\n    """Test Path: happy path"""\n    assert 1 + 1 == 2\n'
            test_file = Path(directory) / "test_sample.py"
            test_file.write_text(source, encoding="utf-8")

            markdown = _render_agent_md_files_for_test_file(test_file)[0][1]

        self.assertIn("Evaluate each criterion in a fresh subagent", markdown)

    def test_creates_pending_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_agent_md_file` creates `single-test packet` with exactly 25 pending scorecard rows.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Filesystem contains `render_agent_md_file` output path.
        File contains 25 pending rows.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_refresh_scenario`
          Justification: Deeper coverage — The current test proves that one renderer output has exactly 25 pending rows. Higher test proves fresh regeneration of both '.agent.md' file types.
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Justification: Deeper coverage — The current test proves that one renderer output has exactly 25 pending rows. Higher test proves selective pending regeneration after source edits.
        - Higher Level Test: `test_load_all_formats.py::test_loads_python_tests`
          Justification: Deeper coverage — The current test directly verifies pending scorecard initialization. `test_load_all_formats.py::test_loads_python_tests` verifies Python extraction and complete file content.
        - Higher Level Test: `test_load_all_formats.py::test_loads_typescript_tests`
          Justification: Deeper coverage — The current test directly verifies pending scorecard initialization. `test_load_all_formats.py::test_loads_typescript_tests` verifies TypeScript extraction and complete file content.
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
        self.assertEqual(25, artifact_text.count("| pending |"))

if __name__ == "__main__":
    unittest.main()
