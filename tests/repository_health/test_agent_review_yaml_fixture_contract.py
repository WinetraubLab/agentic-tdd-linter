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

from tests.agentic_linter.test_harness.single_test_review_yaml_fixture_contract import (
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

            invalid_001:
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
                11: # First Line States a General Behavioral Rule
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
        `test_agent_review_yaml_fixture_contract` emits an unsupported-field error when a YAML example contains any field outside `supported fields`.
        Specialized usage: When one YAML example contains an owner field instead of only `supported fields`, `test_agent_review_yaml_fixture_contract` emits the unsupported-field error.

        Verification Method: verify public function output

        Verification Detail:
        `lint_agent_review_examples` output contains "unsupported field `owner`".
        """

        invalid_source = textwrap.dedent(
            '''
            # Test-source examples for agent review.
            # Each example contains only `file_docstring`, `test`, and `expected_scorecard`.
            # Criteria omitted from `expected_scorecard` are ignored during comparison.
            # Criterion comments must match their titles in `single_test_review.agent.md.j2`.
            # Each outcome must be `pass` or `fail` followed by an explanation comment.

            invalid_001:
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
                11: # First Line States a General Behavioral Rule
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

    def test_rejects_invalid_case_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `test_agent_review_yaml_fixture_contract` requires every YAML case name to combine its filename stem with a three-digit number and permits an optional three-word note.
        Specialized usage: The case in invalid.yaml uses a descriptive name instead of the filename-number format, so YAML validation emits the case-name diagnostic.

        Verification Method: verify public function output

        Verification Detail:
        `lint_agent_review_examples` output requires the pattern `invalid_<three_digit_number>`.

        Similar Coverage:
        - Scenario Difference: `test_relationship_review_yaml_fixture_contract.py::test_rejects_invalid_case_sequence`
          Explanation: The current test verifies `test_agent_review_yaml_fixture_contract` requires every YAML case name to combine its filename stem with a three-digit number and permits an optional three-word note. The named test verifies `test_relationship_review_yaml_fixture_contract` requires every relationship YAML case name to begin with its filename stem, an underscore, and a three-digit number; both use failure path, but exercise materially different scenarios.
        """

        invalid_source = textwrap.dedent(
            '''
            # Test-source examples for agent review.
            # Each example contains only `file_docstring`, `test`, and `expected_scorecard`.
            # Criteria omitted from `expected_scorecard` are ignored during comparison.
            # Criterion comments must match their titles in `single_test_review.agent.md.j2`.
            # Each outcome must be `pass` or `fail` followed by an explanation comment.

            descriptive_name:
              file_docstring: |
                """Document the example source file."""
              test: |
                def test_example() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Addition calculates sums.
                    Standard usage: The scenario demonstrates baseline behavior.

                    Verification Method: verify public function output

                    Verification Detail:
                    The expression produces `2`.
                    """

                    assert 1 + 1 == 2
              expected_scorecard:
                11: # First Line States a General Behavioral Rule
                  pass # The requirement states the calculation behavior.
            '''
        ).lstrip()
        with tempfile.TemporaryDirectory() as directory:
            example_file = Path(directory) / "invalid.yaml"
            example_file.write_text(invalid_source, encoding="utf-8")

            errors = lint_agent_review_examples(examples_path=example_file)

        self.assertTrue(
            any(
                "must be named `invalid_<three_digit_number>`" in error
                for error in errors
            )
        )


if __name__ == "__main__":
    unittest.main()
