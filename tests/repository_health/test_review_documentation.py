"""Verify that contributor guides contain required review commands in workflow order.

Terms:
- `reviewer identity`: A reviewer identity records the agent and model that completed a review. For example, `codex:gpt-5.5` is a reviewer identity.
"""

from __future__ import annotations

import shlex
import unittest
from pathlib import Path


class ReviewDocumentationTests(unittest.TestCase):
    def test_readme_lint_example_includes_reviewer_argument(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        README provides a lint example showcasing the `--reviewer` argument and `reviewer identity`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Parsed arguments equal `lint`, `--reviewer`, and `codex:gpt-5.5` in that order.
        """

        repo_root = Path(__file__).resolve().parents[2]
        reviewer = "codex:gpt-5.5"
        expected_args = ["lint", "--reviewer", reviewer]
        self.assertEqual(_readme_review_command_args(repo_root), expected_args)

