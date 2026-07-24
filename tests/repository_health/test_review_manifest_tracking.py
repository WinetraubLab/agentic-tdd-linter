"""Tests in this file validate `test_review_manifest_tracking` located at `tests/repository_health/test_review_manifest_tracking.py`.
`test_review_manifest_tracking` is responsible for requiring repository review artifacts in source control.

Terms:
- `self-lint review record`: A self-lint review record is a tracked agent-review proof file. For example, `tests/agentic_review_manifest.jsonl` stores repository self-lint proof, while `temporary_fixtures/agentic_review_manifest.jsonl` stores integration-scenario proof.
- `YAML-example lint review record`: A YAML-example lint review record stores the latest completed YAML-example results. For example, `tests/agentic_linter/test_agent_review_example_runner.json` is a YAML-example lint review record.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class ReviewManifestTrackingTests(unittest.TestCase):
    def test_review_manifest_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Repository source control retains `review manifest` at tests/agentic_review_manifest.jsonl as a tracked file.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Source control maintains `tests/agentic_review_manifest.jsonl`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = _tracked_result(
            Path("tests") / "agentic_review_manifest.jsonl",
            repo_root=repo_root,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_e2e_manifest_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Repository source control retains `E2E manifest` at temporary_fixtures/agentic_review_manifest.jsonl as a tracked file.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Source control maintains `temporary_fixtures/agentic_review_manifest.jsonl`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        result = _tracked_result(
            Path("temporary_fixtures") / "agentic_review_manifest.jsonl",
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
