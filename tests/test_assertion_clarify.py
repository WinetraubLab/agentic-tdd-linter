from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import run_linter_with_review


class AssertionClarifyTests(unittest.TestCase):
    def test_extra_assertion_fails_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Extra result assertions fail when they prove behavior outside the requirement.

        Verification Method: verify public function output

        Verification Detail:
        Output includes Assertion Purpose Check.
        """

        test_body = """
            a = 1
            b = 2
            c = add_2_positive_numbers(a, b)
            assert c > 0
            assert c == a + b
        """

        result = run_linter_with_review(
            requirement="Adding positive numbers returns a positive result.",
            test_body=test_body,
            status="fail",
            note=(
                "Assertion Purpose Check: Fail. `assert c == a + b` proves "
                "exact-sum behavior instead of the positive-result requirement."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Assertion Purpose Check", result.output)

    def test_tagged_input_assertions_pass(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agentic review accepts input assertions marked with `# Input check`.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the reviewed artifact lets the linter exit successfully.
        """

        test_body = """
            a = 1
            b = 2
            c = add_2_positive_numbers(a, b)
            assert a > 0  # Input check
            assert b > 0  # Input check
            assert c > 0
        """

        result = run_linter_with_review(
            requirement="Adding positive numbers returns a positive result.",
            test_body=test_body,
            status="pass",
            note="Assertion Purpose Check: Pass.",
        )

        self.assertEqual(0, result.exit_code)

    def test_untagged_input_assertions_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic review rejects input assertions without required tags.

        Verification Method: verify public function output

        Verification Detail:
        by asserting failed review output names missing input tags.
        """

        test_body = """
            a = 1
            b = 2
            c = add_2_positive_numbers(a, b)
            assert a > 0
            assert b > 0
            assert c > 0
        """

        result = run_linter_with_review(
            requirement="Adding positive numbers returns a positive result.",
            test_body=test_body,
            status="fail",
            note=(
                "Assertion Purpose Check: Fail. `assert a > 0` and "
                "`assert b > 0` need `# Input check` tags."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("# Input check", result.output)

if __name__ == "__main__":
    unittest.main()
