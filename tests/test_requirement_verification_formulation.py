from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class RequirementVerificationFormulationTests(unittest.TestCase):
    def test_narrow_requirement_examples_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Narrow requirements fail when examples replace behavior.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes too-narrow guidance.
        """

        # Problem sentence: requirement names test functions instead of behavior.
        test_names_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `test_normalizes_name` and `test_normalizes_city` fail until each requirement names specific behavior.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=test_names_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names assertion mechanics instead of behavior.
        assertion_mechanics_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Input assertions pass when `assert a > 0` and `assert b > 0` include `# Input check` tags.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=assertion_mechanics_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names `EXPECTED_VALUE` instead of behavior.
        expected_value_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `EXPECTED_VALUE` fails when it supplies function input outside the test body.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=expected_value_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names test levels instead of behavior.
        test_level_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `test_sum_public` and `test_sum_private` fail without mutual `see also` references.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=test_level_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names another test instead of behavior.
        swappable_requirement_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `test_bad_sentence_structure` fails because `test_sentence_has_verb` could use the same requirement.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=swappable_requirement_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

    def test_verification_mechanics_only_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Verification details describe behavior evidence.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes behavior-level evidence.
        """

        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Adding two numbers must yield positive result.

                    Verification Method: verify public function output

                    Verification Detail:
                    by running the check command with a pass artifact and asserting success.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("behavior-level evidence", reason)

    def test_verification_bare_output_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Verification details connect linter output to behavior.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes behavior context.
        """

        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Adding two numbers must yield positive result.

                    Verification Method: verify public function output

                    Verification Detail:
                    Exit code is zero.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("behavior context", reason)

    def test_ambiguous_data_flow_terms_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Data-flow terms require named owners.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes ambiguous data-flow guidance.
        """

        # Problem sentence: "input" has no named owner.
        input_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                The input is normalized before validation.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=input_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("input", reason)

        # Problem sentence: "output" has no named owner.
        output_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                The output includes the normalized value.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=output_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("output", reason)

        # Problem sentence: "returns" has no named owner.
        returns_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                The parser returns the expected value.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=returns_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("returns", reason)

        # Problem sentence: "Output" has no named owner.
        capital_output_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Adding two numbers must yield positive result.

                Verification Method: verify public function output

                Verification Detail:
                Output cites missing tags.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=capital_output_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("Output", reason)

        # Problem sentence: "provided" does not name who provides the activity name.
        provided_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Add an artifact row from a template using the provided activity name.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=provided_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("provided", reason)


if __name__ == "__main__":
    unittest.main()
