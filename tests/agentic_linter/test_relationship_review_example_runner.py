"""Tests in this file validate `relationship_review_example_runner` located at `tests/agentic_linter/test_harness/relationship_review_example_runner.py`.
`relationship_review_example_runner` is responsible for converting relationship YAML examples for the shared review runner.

Terms:
- `relationship review case`: One unordered test pair with expected overlap and difference kind.
- `relationship YAML catalog`: Docstring-pair examples and their expected classifications.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.agentic_linter.test_harness.relationship_review_example_runner import (
    EXAMPLES,
    _relationship_review_cases,
)
from tests.agentic_linter.test_harness.relationship_review_yaml_fixture_contract import (
    DIFFERENCE_KINDS,
)


class TestRelationshipReviewExampleRunnerTests(unittest.TestCase):
    def test_builds_relationship_review_cases(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `relationship_review_example_runner` converts the `relationship YAML catalog` into `relationship review case` records for the shared runner.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The runner produces one case per catalog example and one review input per case.
        Every case identifies one unordered pair and records an overlap expectation.
        Each overlapping case records an allowed difference kind, while each nonoverlapping case omits the difference kind.
        Every case locates its packet under the supplied artifact root.

        Similar Coverage:
        - Module Difference: `test_agent_review_example_runner.py::test_builds_single_test_review_cases`
          Explanation: The current test verifies `relationship_review_example_runner` converts the `relationship YAML catalog` into `relationship review case` records for the shared runner. The named test verifies `agent_review_example_runner` converts the `YAML fixture catalog` into `single-test review case` records for the shared runner; both exercise materially the same scenario through different named modules or contract subjects.
        """

        with tempfile.TemporaryDirectory() as directory:
            artifact_root = Path(directory) / "artifacts"
            examples, cases, review_inputs = _relationship_review_cases(
                EXAMPLES,
                artifact_root,
            )

        self.assertEqual(len(examples), len(cases))
        self.assertEqual(len(cases), len(review_inputs))
        self.assertTrue(
            all(case.test_name.count(" <> ") == 1 for case in cases)
        )
        self.assertTrue(
            all(case.expected_scorecard[10] in {"yes", "no"} for case in cases)
        )
        self.assertTrue(
            all(
                case.expected_scorecard.get(11) in DIFFERENCE_KINDS
                if case.expected_scorecard[10] == "yes"
                else 11 not in case.expected_scorecard
                for case in cases
            )
        )
        self.assertTrue(
            all(case.artifact_path.parent == artifact_root for case in cases)
        )


if __name__ == "__main__":
    unittest.main()
