"""Run repository YAML examples through anonymous agent review.

This module contains the review runner, separate from deterministic harness
tests. The runner does not judge criteria itself. It renders anonymous
`.agent.md` files and stops while external reviews are pending. After reviewers
complete those files, rerunning the test compares their scorecards with the
YAML expectations and reports regressions.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.agentic_linter.test_harness.agent_review_example_runner import (
    REPO_ROOT,
    run_agent_review_examples,
)


class AgentReviewExampleRunnerTests(unittest.TestCase):
    def test_anonymous_agent_review_examples(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agentic linter validates completed anonymous reviews against repository YAML expectations.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        1. Select the repository YAML examples for single-test review.
        2. Run the anonymous agent-review example harness.
        3. If reviews are pending, review the generated '.agent.md' files and rerun this test.
        4. Verify that completed scorecards match the YAML expectations without regressions.
        Completion produces `None`.
        """

        examples_relative_path = Path(
            "tests/agentic_linter/fixtures/single_test_review"
        )
        reviewer_model = "5.6 Sol Medium"
        examples_path = REPO_ROOT / examples_relative_path

        result = run_agent_review_examples(
            examples_path=examples_path,
            reviewer_model=reviewer_model,
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
