from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.cli import main
from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_ran_proof import (
    lint_agent_review_artifact,
    source_sha256,
)
from agentic_tdd_linter.agentic_md import write_agentic_md_for_test_file


class AgentReviewArtifactTests(unittest.TestCase):
    def test_accepts_reviewed_pass_artifact(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        When the SHA matches the test file, `Status: pass` is accepted.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the reviewed pass artifact returns an empty issue list.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact = _write_artifact(root, test_file, status="pass")

            issues = lint_agent_review_artifact(test_file, artifact, root)

        self.assertEqual([], issues)

    def test_accepts_default_artifact(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts a pass artifact from `tests/agentic_review_artifacts`.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the default pass artifact returns an empty issue list.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_artifact(
                root,
                test_file,
                status="pass",
                artifact_path=agent_review_artifact_path(test_file, root),
            )

            issues = lint_agent_review_artifact(test_file, repo_root=root)

        self.assertEqual([], issues)

    def test_reports_pending_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Pending artifact emits incomplete-review issue.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `agent_review_not_run` is reported for pending status.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact = _write_artifact(root, test_file, status="pending")

            rules = _issue_rules(lint_agent_review_artifact(test_file, artifact, root))

        self.assertIn("agent_review_not_run", rules)

    def test_reports_unreviewed_generated_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Untouched generated artifact emits incomplete-review issue.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `agent_review_not_run` is reported for the generated pending artifact.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            write_agentic_md_for_test_file(test_file, root)

            rules = _issue_rules(lint_agent_review_artifact(test_file, repo_root=root))

        self.assertIn("agent_review_not_run", rules)

