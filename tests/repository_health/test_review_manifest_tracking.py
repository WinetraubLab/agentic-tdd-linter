"""Verify that agent-review manifests remain tracked.

Terms:
- `review manifest`: A review manifest is the tracked proof file for repository test reviews. For example, `tests/agentic_review_manifest.jsonl` is a review manifest.
- `E2E manifest`: An E2E manifest stores agent-review proof for generated end-to-end scenarios. For example, `temporary_fixtures/agentic_review_manifest.jsonl` preserves proof between workflow runs.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class ReviewManifestTrackingTests(unittest.TestCase):
    def test_review_manifest_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Git classifies `review manifest` at tests/agentic_review_manifest.jsonl as tracked.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Git classifies manifest path as tracked.
        Query code equals `0`.
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
        Git classifies `E2E manifest` at temporary_fixtures/agentic_review_manifest.jsonl as tracked.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Git classifies manifest path as tracked.
        Query code equals `0`.
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
