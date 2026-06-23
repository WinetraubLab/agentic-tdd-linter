from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_review_manifest import (
    agent_review_manifest_path,
    review_contract_sha256,
)
from agentic_tdd_linter.agent_ran_proof import source_sha256
from agentic_tdd_linter.cli import main
from agentic_tdd_linter.version import __version__


REVIEWER = "codex:gpt-5.5"


class ReviewProofFlowTests(unittest.TestCase):
    def test_check_accepts_current_manifest(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Manifest proof satisfies attestation checks. Linter skips artifacts.

        Verification Method: verify public function output

        Verification Detail:
        Run automatic proof mode with a matching manifest and assert no artifact is created.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact_path = agent_review_artifact_path(test_file, root)
            _write_manifest(root, test_file, source_hash=source_sha256(test_file))
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            artifact_exists = artifact_path.exists()

        self.assertEqual(0, exit_code)
        self.assertFalse(artifact_exists)
        self.assertIn("no issues found", stdout.getvalue())

    def test_check_creates_missing_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Missing `review manifest` causes linter to create artifacts.

        Verification Method: verify public function output

        Verification Detail:
        Run check without a manifest and assert pending artifact is created.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact_path = agent_review_artifact_path(test_file, root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            artifact_exists = artifact_path.is_file()

        self.assertEqual(1, exit_code)
        self.assertTrue(artifact_exists)
        self.assertIn("agent_review_not_run", stdout.getvalue())

