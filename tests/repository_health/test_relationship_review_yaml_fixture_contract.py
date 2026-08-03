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
        `test_relationship_review_yaml_fixture_contract` requires every relationship YAML case name to combine its filename stem with its three-digit sequence number and permits an optional three-word note.
        Specialized usage: The first case in similar_coverage.yaml uses a descriptive name instead of `similar_coverage_001`, so schema validation emits the case-name diagnostic.

        Verification Method: verify public function output

        Verification Detail:
        `lint_test_relationship_review_examples` output requires the name `similar_coverage_001`.
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
            any("must be named `similar_coverage_001`" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
