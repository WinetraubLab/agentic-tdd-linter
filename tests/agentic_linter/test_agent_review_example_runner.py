"""Tests in this file validate `agent_review_example_runner` located at `tests/agentic_linter/test_harness/agent_review_example_runner.py`.
`agent_review_example_runner` is responsible for converting single-test YAML examples for the shared review runner.

Terms:
- `single-test review case`: One extracted test and its expected scorecard.
- `YAML fixture catalog`: Single-test examples and their expected scorecards.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.agentic_linter.test_harness import agent_review_example_runner as runner_harness
from tests.agentic_linter.test_harness.agent_review_example_runner import (
    REPO_ROOT,
    _single_test_review_cases,
)


class AgentReviewExampleRunnerTests(unittest.TestCase):
    def test_builds_single_test_review_cases(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_example_runner` converts the `YAML fixture catalog` into `single-test review case` records for the shared runner.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Mocking redirects runner output paths to the temporary artifact directory.
        Every case has one extracted test, source digest, pass/fail expectations, and packet path.

        Similar Coverage:
        - Module Difference: `test_relationship_review_example_runner.py::test_builds_relationship_review_cases`
          Explanation: The current test verifies `agent_review_example_runner` converts the `YAML fixture catalog` into `single-test review case` records for the shared runner. The named test verifies `relationship_review_example_runner` converts the `relationship YAML catalog` into `relationship review case` records for the shared runner; both exercise materially the same scenario through different named modules or contract subjects.
        """

        examples_path = (
            REPO_ROOT / "tests/agentic_linter/fixtures/single_test_review"
        )
        with tempfile.TemporaryDirectory() as directory:
            anonymous_root = Path(directory) / "agent_review_examples"
            artifact_root = anonymous_root / "agentic_review_artifacts"
            with mock.patch.multiple(
                runner_harness,
                ANONYMOUS_ROOT=anonymous_root,
                ARTIFACT_ROOT=artifact_root,
            ):
                examples, cases, review_inputs = _single_test_review_cases(
                    examples_path
                )

        self.assertTrue(examples)
        self.assertEqual(len(cases), len(review_inputs))
        self.assertTrue(
            all(case.completed_results == ("pass", "fail") for case in cases)
        )
        self.assertTrue(
            all(
                set(case.expected_scorecard.values()) <= {"pass", "fail"}
                for case in cases
            )
        )
        self.assertTrue(
            all(len(case.source_sha256) == 64 for case in cases)
        )
        self.assertTrue(
            all(case.artifact_path.parent == artifact_root for case in cases)
        )


if __name__ == "__main__":
    unittest.main()
