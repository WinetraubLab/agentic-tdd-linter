"""Tests in this file validate `render_cross_test_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/render_cross_test_agent_md_file.py`.
`render_cross_test_agent_md_file` is responsible for creating an isolated cross-test `.agent.md` that documents test-coverage relationships.

Terms:
- `renderer`: The renderer creates a cross-test review packet from selected paths. For example, it writes one packet for two test files.
- `cross-test packet`: A cross-test packet contains review context for relationships among tests. For example, it lists test files and Similar Coverage instructions.
- `relationship fields`: Relationship fields encode higher references, lower references, and classified justifications. For example, one pair names both test levels and its coverage difference.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_tdd_linter.agentic_linter.render_cross_test_agent_md_file import (
    _build_cross_test_review_scope,
    render_cross_test_agent_md_file,
)


class CrossTestAgentMarkdownTests(unittest.TestCase):
    def test_deduplicates_cross_test_paths(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` retains every unique selected path exactly once.
        Specialized usage: Selected paths contain one duplicate path instead of only unique paths.

        Verification Method: verify private function output

        Verification Detail:
        Packet contains path `tests/test_alpha.py`.
        Packet contains path `tests/test_beta.py`.
        Packet contains each path once.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_example():\n    assert True\n"
            first = root / "tests" / "test_alpha.py"
            second = root / "tests" / "test_beta.py"
            first.parent.mkdir(parents=True)
            first.write_text(source, encoding="utf-8")
            second.write_text(source, encoding="utf-8")

            scope = _build_cross_test_review_scope(
                [first, second, first],
                root,
            )

        self.assertCountEqual(["tests/test_alpha.py", "tests/test_beta.py"], scope)
        self.assertEqual(2, len(scope))

    def test_instructions_limit_review_to_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` constrains `cross-test packet` context to the packet and listed files.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `Review context is limited to this packet and the listed test files.`
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn(
            "Review context is limited to this packet and the listed test files.",
            artifact_text,
        )

    def test_requires_overlap_explanations(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` requires `relationship fields` to provide a coverage classification and a specific coverage-difference explanation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `Justification: <classification> — <specific coverage difference>`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn(
            "Justification: <classification> — <specific coverage difference>",
            artifact_text,
        )

    def test_requires_reciprocal_references(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` requires `relationship fields` to identify both tests in each higher-level/lower-level pair.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `A passing pair provides reciprocal references and justifications in both tests.`
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn(
            "A passing pair provides reciprocal references",
            artifact_text,
        )

    def test_instructions_show_similar_coverage_format(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` shows how `relationship fields` represent a higher-level test, lower-level test, and coverage-difference justification.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Packet contains ``Higher Level Test: `<file.py>::<test_name>```.
        Packet contains ``Lower Level Test: `<file.py>::<test_name>```.
        Packet contains `Justification: <classification> — <specific coverage difference>`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn("Higher Level Test: `<file.py>::<test_name>`", artifact_text)
        self.assertIn("Lower Level Test: `<file.py>::<test_name>`", artifact_text)
        self.assertIn(
            "Justification: <classification> — <specific coverage difference>",
            artifact_text,
        )


if __name__ == "__main__":
    unittest.main()
