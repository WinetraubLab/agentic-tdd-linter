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
        `test_review_manifest_tracking` requires source control to track `YAML-example lint report`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Git index contains `tests/agentic_linter/test_agent_review_example_runner.json`.
        `_tracked_result` exit code equals `0`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = _tracked_result(
            Path("tests")
            / "agentic_linter"
            / "test_agent_review_example_runner.json",
            repo_root=repo_root,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_yaml_review_proof_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_manifest_tracking` requires source control to track `YAML-example lint proof`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Git index contains `tests/agentic_linter/test_agent_review_example_runner.jsonl`.
        `_tracked_result` exit code equals `0`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = _tracked_result(
            Path("tests")
            / "agentic_linter"
            / "test_agent_review_example_runner.jsonl",
            repo_root=repo_root,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_self_lint_record_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_manifest_tracking` requires source control to track `self-lint review record`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Git index contains `tests/agentic_review_manifest.jsonl`.
        `_tracked_result` exit code equals `0`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = _tracked_result(
            Path("tests") / "agentic_review_manifest.jsonl",
            repo_root=repo_root,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)


def _tracked_result(
    path: Path,
    *,
    repo_root: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


if __name__ == "__main__":
    unittest.main()
