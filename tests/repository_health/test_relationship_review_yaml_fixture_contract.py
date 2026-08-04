"""Tests in this file validate `test_relationship_review_yaml_fixture_contract` located at `tests/repository_health/test_relationship_review_yaml_fixture_contract.py`.
`test_relationship_review_yaml_fixture_contract` is responsible for enforcing repository policy for maintainable test-relationship YAML examples.

"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.agentic_linter.test_harness.relationship_review_yaml_fixture_contract import (
    EXAMPLES,
    lint_test_relationship_review_examples,
)


class RelationshipReviewYamlFixtureContractTests(unittest.TestCase):
    def test_rejects_invalid_case_sequence(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `test_relationship_review_yaml_fixture_contract` requires every relationship YAML case name to begin with its filename stem, an underscore, and a three-digit number.
        Specialized usage: When similar_coverage.yaml contains a case name without the required filename-number prefix, `test_relationship_review_yaml_fixture_contract` emits the case-name diagnostic.

        Verification Method: verify public function output

        Verification Detail:
        `lint_test_relationship_review_examples` output contains a diagnostic requiring the pattern `similar_coverage_<three_digit_number>`.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_yaml_fixture_contract.py::test_rejects_invalid_case_name`
          Explanation: The current test verifies `test_relationship_review_yaml_fixture_contract` requires every relationship YAML case name to begin with its filename stem, an underscore, and a three-digit number. The named test verifies `test_agent_review_yaml_fixture_contract` requires every YAML case name to combine its filename stem with a three-digit number and permits an optional three-word note; both use failure path, but exercise materially different scenarios.
        """

        source_path = EXAMPLES / "similar_coverage.yaml"
        invalid_source = source_path.read_text(encoding="utf-8").replace(
            "similar_coverage_001_happy_failure_difference:",
            "descriptive_name:",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            example_file = Path(directory) / "similar_coverage.yaml"
            example_file.write_text(invalid_source, encoding="utf-8")

            errors = lint_test_relationship_review_examples(
                examples_path=example_file
            )

        self.assertTrue(
            any(
                "must be named `similar_coverage_<three_digit_number>`" in error
                for error in errors
            )
        )


if __name__ == "__main__":
    unittest.main()
