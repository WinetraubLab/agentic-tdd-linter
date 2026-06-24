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

        result = run_linter_with_review(
            verification_detail=(
                "by running the check command with a pass artifact and "
                "asserting success."
            ),
            status="fail",
            note=(
                "Verification Formulation Check: Fail. Verification Detail "
                "describes mechanics instead of behavior-level evidence."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("behavior-level evidence", result.output)

    def test_verification_bare_output_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Verification details connect linter output to behavior.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes behavior context.
        """

        result = run_linter_with_review(
            verification_detail="Exit code is zero.",
            status="fail",
            note=(
                "Verification Formulation Check: Fail. `Exit code is zero` "
                "states a bare observation without behavior context."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("behavior context", result.output)

    def test_ambiguous_data_flow_terms_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Data-flow terms require named owners.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes ambiguous data-flow guidance.
        """

        cases = [
            (
                "input",
                {"requirement": "The input is normalized before validation."},
                (
                    "Convoluted Wording Check: Fail. `input` is ambiguous "
                    "because the requirement does not name which function owns "
                    "the value."
                ),
                "input",
            ),
            (
                "output",
                {"requirement": "The output includes the normalized value."},
                (
                    "Convoluted Wording Check: Fail. `output` is ambiguous "
                    "because the requirement does not name which function owns "
                    "the value."
                ),
                "output",
            ),
            (
                "returns",
                {"requirement": "The parser returns the expected value."},
                (
                    "Convoluted Wording Check: Fail. `returns` is ambiguous "
                    "because the requirement does not name the specific parser "
                    "function."
                ),
                "returns",
            ),
            (
                "verification output",
                {"verification_detail": "Output cites missing tags."},
                (
                    "Convoluted Wording Check: Fail. `Output` is ambiguous "
                    "because the verification detail does not name the linter "
                    "report."
                ),
                "Output",
            ),
            (
                "provided activity name",
                {
                    "requirement": (
                        "Add an artifact row from a template using the "
                        "provided activity name."
                    )
                },
                (
                    "Convoluted Wording Check: Fail. `provided` is ambiguous "
                    "because the requirement does not name which caller or "
                    "fixture supplies the activity name."
                ),
                "provided",
            ),
        ]

        for label, linter_kwargs, note, expected_text in cases:
            with self.subTest(label=label):
                result = run_linter_with_review(
                    **linter_kwargs,
                    status="fail",
                    note=note,
                )

                self.assertEqual(1, result.exit_code)
                self.assertIn("agent_review_failed", result.output)
                self.assertIn("ambiguous", result.output)
                self.assertIn(expected_text, result.output)

if __name__ == "__main__":
    unittest.main()
