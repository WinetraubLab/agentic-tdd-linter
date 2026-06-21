from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import run_linter_source_with_review, run_linter_with_review


class SelfContainedValueTests(unittest.TestCase):
    def test_external_expected_value_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Expected values require local definitions. Shared constants hide checked values.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Keep Assertions Self-Contained.
        """

        test_body = """
            expected_value = EXPECTED_VALUE
            assert(fun_a(10), expected_value)
        """

        result = run_linter_with_review(
            requirement="Function `fun_a` returns the expected value for ten.",
            test_body=test_body,
            status="fail",
            note=(
                "Keep Assertions Self-Contained: Fail. `EXPECTED_VALUE` is "
                "not defined in the test body."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Keep Assertions Self-Contained", result.output)

    def test_external_argument_value_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Function argument values require local definitions.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Keep Assertions Self-Contained.
        """

        test_body = """
            assert(fun_a(EXPECTED_VALUE), 10)
        """

        result = run_linter_with_review(
            requirement="Function `fun_a` returns ten for the provided value.",
            test_body=test_body,
            status="fail",
            note=(
                "Keep Assertions Self-Contained: Fail. `EXPECTED_VALUE` is "
                "used as an argument but is not defined in the test body."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Keep Assertions Self-Contained", result.output)

    def test_external_requirement_value_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Requirement values require local definitions.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Keep Assertions Self-Contained.
        """

        source = '''
            def test_long_requirement_fails() -> None:
                """Test Path: failure path

                Requirement Tested:
                Linter rejects long requirements.

                Verification Method: verify public function output

                Verification Detail:
                Linter report includes Sentence Checks.
                """

                requirement = _five_sentence_requirement()
                result = run_linter_with_review(
                    requirement=requirement,
                    status="fail",
                    note="Sentence Checks: Fail. Requirement is too long.",
                )

                assert result.exit_code == 1


            def _five_sentence_requirement() -> str:
                return "Parser accepts positive numbers safely."
        '''

        result = run_linter_source_with_review(
            source=source,
            status="fail",
            note=(
                "Keep Assertions Self-Contained: Fail. `requirement=` comes "
                "from `_five_sentence_requirement`, which is outside the test body."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("outside the test body", result.output)


if __name__ == "__main__":
    unittest.main()
