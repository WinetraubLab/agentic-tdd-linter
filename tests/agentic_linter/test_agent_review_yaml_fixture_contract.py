"""Verify the repository's agent-review YAML fixture contract."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from .agent_review_yaml_fixture_contract import EXAMPLES, lint_agent_review_examples


class AgentReviewYamlFixtureContractTests(unittest.TestCase):
    def test_accepts_repository_fixtures(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agent-review YAML fixtures satisfy the repository contract.
        This applies to every YAML file in the fixture folder.

        Verification Method: verify public function output

        Verification Detail:
        The schema result contains no errors.
        """

        self.assertEqual([], lint_agent_review_examples(examples_path=EXAMPLES))

    def test_result_requires_explanation(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Expected scorecard outcomes require explanation comments.
        This applies when a fixture declares `pass` or `fail` without a rationale.

        Verification Method: verify public function output

        Verification Detail:
        The schema linter identifies the missing explanation comment.
        """

        source = (EXAMPLES / "requirement_formulation.yaml").read_text(encoding="utf-8")
        invalid_source = source.replace(
            "fail # The requirement lists availability examples without stating a general behavior.",
            "fail",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            case_file = Path(directory) / "invalid.yaml"
            case_file.write_text(invalid_source, encoding="utf-8")
            errors = lint_agent_review_examples(examples_path=case_file)

        self.assertEqual(1, len(errors))
        self.assertIn("fail needs an explanation comment", errors[0])

    def test_rejects_unsupported_fields(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agent-review examples allow only two fields.
        This applies when an example adds a field besides `test` or `expected_scorecard`.

        Verification Method: verify public function output

        Verification Detail:
        The schema linter names the unsupported field and the allowed fields.
        """

        source = (EXAMPLES / "requirement_formulation.yaml").read_text(encoding="utf-8")
        invalid_source = source.replace(
            "availability_without_behavior:\n  test: |",
            "availability_without_behavior:\n  owner: parser\n  test: |",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            example_file = Path(directory) / "invalid.yaml"
            example_file.write_text(invalid_source, encoding="utf-8")
            errors = lint_agent_review_examples(examples_path=example_file)

        self.assertEqual(1, len(errors))
        self.assertIn("unsupported field `owner`", errors[0])
        self.assertIn("only `test` and `expected_scorecard` are allowed", errors[0])


if __name__ == "__main__":
    unittest.main()
