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
        Agentic linter marks every review criterion as pending in a newly generated single-test `.agent.md`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The returned path identifies an existing `.agent.md` file.
        The file contains `24` pending scorecard rows.
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
        self.assertEqual(24, artifact_text.count("| pending |"))

if __name__ == "__main__":
    unittest.main()
