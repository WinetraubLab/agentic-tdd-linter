"""Verify rendering of cross-test review packets.

Terms:
- `renderer`: The renderer creates a cross-test review packet from selected paths. For example, it writes one packet for two test files.
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
        Agentic linter deduplicates cross-test paths.
        Specialized usage: For duplicate removal, packet path becomes repeated
        (instead of unique).

        Verification Method: verify private function output

        Verification Detail:
        The packet contains these paths:
        `tests/test_alpha.py`
        `tests/test_beta.py`
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
        Cross-test `.agent.md` includes an instruction to use only the `.agent.md` packet and its listed test files as review context.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The cross-test `.agent.md` file contains this instruction:
        `Use only this packet and the listed test files as review context.`
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
            "Use only this packet and the listed test files as review context.",
            artifact_text,
        )

    def test_instructions_require_both_tests_to_explain_overlap(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Cross-test `.agent.md` instructions require both tests in a cross-level pair to reference each other and explain their coverage difference.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The cross-test `.agent.md` file contains this instruction:
        `A passing pair includes reciprocal references and justifications`
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
            "A passing pair includes reciprocal references and justifications",
            artifact_text,
        )


        Requirement Tested:
        The `renderer` validates paths.
        When a path is not a test, it rejects the file.

        Verification Method: verify public function output

        Verification Detail:
        `ValueError` identifies `test_*.py`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_file = root / "tests" / "helper.py"
            source_file.parent.mkdir(parents=True)
            source_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, r"requires test_\*\.py files"):
                render_cross_test_agent_md_file([source_file], root)
