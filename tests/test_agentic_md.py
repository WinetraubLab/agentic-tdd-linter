from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_ran_proof import source_sha256
from agentic_tdd_linter.agentic_md import agentic_md_for_test_file, write_agentic_md_for_test_file


class AgenticMarkdownTests(unittest.TestCase):
    def test_includes_review_instructions(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` includes generic requirement, jargon, assertion, and level checks.

        Verification Method: verify public function output

        Verification Detail:
        Markdown includes each checked heading.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("Notify Generic Requirement", markdown)
        self.assertIn("Notify Convoluted Wording", markdown)
        self.assertIn("test-specific jargon", markdown)
        self.assertIn("backticked", markdown)
        self.assertIn("Review markdown", markdown)
        self.assertIn("agent_review_artifact", markdown)
        self.assertIn("Focus on What is Being Verified, Not How", markdown)
        self.assertIn("behavior level", markdown)
        self.assertIn("behavior-level evidence", markdown)
        self.assertIn("Assertion Purpose Check", markdown)
        self.assertIn("Keep Assertions Self-Contained", markdown)
        self.assertIn("requirement=", markdown)
        self.assertIn("Test Level Redundancy Check", markdown)
