"""Tests in this file validate `test_agent_review_yaml_fixture_contract` located at `tests/repository_health/test_agent_review_yaml_fixture_contract.py`.
`test_agent_review_yaml_fixture_contract` is responsible for enforcing repository policy for maintainable agent-review YAML examples.

Terms:
- `supported fields`: Supported fields are file_docstring, test, and expected_scorecard. For example, an owner field is outside the supported fields.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.agentic_linter.test_harness.agent_review_yaml_fixture_contract import (
    lint_agent_review_examples,
)


class AgentReviewYamlFixtureContractTests(unittest.TestCase):
    def test_result_requires_explanation(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `test_agent_review_yaml_fixture_contract` requires an explanation comment when any scorecard result has fail status.
        Specialized usage: One expected fail result omits its explanation comment, so YAML validation emits the named diagnostic.

        Verification Method: verify public function output

        Verification Detail:
        Validation errors contain `fail needs an explanation comment`.
        """

        invalid_source = textwrap.dedent(
            '''
            # Test-source examples for agent review.
            # Each example contains only `file_docstring`, `test`, and `expected_scorecard`.
            # Criteria omitted from `expected_scorecard` are ignored during comparison.
            # Criterion comments must match their titles in `single_test_review.agent.md.j2`.
            # Each outcome must be `pass` or `fail` followed by an explanation comment.

            missing_comment:
              file_docstring: |
                """Document the example source file."""
              test: |
                def test_example() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Addition calculates sums.
                    When operands contain integers, addition calculates sums.

                    Verification Method: verify public function output

                    Verification Detail:
                    The expression produces `2`.
                    """

                    assert 1 + 1 == 2
              expected_scorecard:
                11: # First Sentence Describes Behavior
                  fail
            '''
        ).lstrip()
        with tempfile.TemporaryDirectory() as directory:
            case_file = Path(directory) / "invalid.yaml"
            case_file.write_text(invalid_source, encoding="utf-8")
            errors = lint_agent_review_examples(examples_path=case_file)

        self.assertTrue(
            any("fail needs an explanation comment" in error for error in errors)
        )

    def test_rejects_unsupported_fields(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `test_agent_review_yaml_fixture_contract` emits an unsupported-field error when any field is outside `supported fields`.
        Specialized usage: One YAML example contains an owner field instead of only `supported fields`, so validation emits the unsupported-field error.

        Verification Method: verify public function output

        Verification Detail:
        Validation errors contain "unsupported field `owner`".
        """

        invalid_source = textwrap.dedent(
            '''
            # Test-source examples for agent review.
            # Each example contains only `file_docstring`, `test`, and `expected_scorecard`.
            # Criteria omitted from `expected_scorecard` are ignored during comparison.
            # Criterion comments must match their titles in `single_test_review.agent.md.j2`.
            # Each outcome must be `pass` or `fail` followed by an explanation comment.

            unsupported_owner:
              owner: parser
              test: |
                def test_example() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Addition calculates sums.
                    When operands contain integers, addition calculates sums.

                    Verification Method: verify public function output

                    Verification Detail:
                    The expression produces `2`.
                    """

                    assert 1 + 1 == 2
              expected_scorecard:
                11: # First Sentence Describes Behavior
                  pass # The requirement states the calculation behavior.
            '''
        ).lstrip()
        with tempfile.TemporaryDirectory() as directory:
            example_file = Path(directory) / "invalid.yaml"
            example_file.write_text(invalid_source, encoding="utf-8")
            errors = lint_agent_review_examples(examples_path=example_file)

        matching_errors = [
            error for error in errors if "unsupported field `owner`" in error
        ]
        self.assertTrue(matching_errors)


if __name__ == "__main__":
    unittest.main()
