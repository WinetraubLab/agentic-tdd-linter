"""Tests in this file validate `test_review_manifest_tracking` located at `tests/repository_health/test_review_manifest_tracking.py`.
`test_review_manifest_tracking` is responsible for requiring repository review artifacts in source control.

Terms:
- `self-lint review record`: The self-lint review record is the repository file at `tests/agentic_review_manifest.jsonl`.
- `YAML-example lint report`: The YAML-example lint report is the readable result file at `tests/agentic_linter/test_agent_review_example_runner.json`.
- `YAML-example lint proof`: The YAML-example lint proof is the attestation file at `tests/agentic_linter/test_agent_review_example_runner.jsonl`.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class ReviewManifestTrackingTests(unittest.TestCase):
    def test_yaml_review_report_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_manifest_tracking` requires Git's index to contain `YAML-example lint report`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Git index contains `tests/agentic_linter/test_agent_review_example_runner.json`.
        `git ls-files --error-unmatch` produces exit code `0`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                "tests/agentic_linter/test_agent_review_example_runner.json",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_yaml_review_proof_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_manifest_tracking` requires Git's index to contain `YAML-example lint proof`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Git index contains `tests/agentic_linter/test_agent_review_example_runner.jsonl`.
        `git ls-files --error-unmatch` produces exit code `0`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                "tests/agentic_linter/test_agent_review_example_runner.jsonl",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_self_lint_record_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_manifest_tracking` requires Git's index to contain `self-lint review record`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Git index contains `tests/agentic_review_manifest.jsonl`.
        `git ls-files --error-unmatch` produces exit code `0`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                "tests/agentic_review_manifest.jsonl",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

if __name__ == "__main__":
    unittest.main()
