from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import run_linter_with_review


class DocstringClarityTests(unittest.TestCase):
    def test_clear_docstring_passes_review(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Sentence structure passes for a simple requirement.

        Verification Method: verify public function output

        Verification Detail:
        by running the check command with a pass artifact and asserting success.
        """

        result = run_linter_with_review(
            status="pass",
            note="Noun Density Check: Pass.",
        )

        self.assertEqual(0, result.exit_code)

    def test_dense_requirement_fails_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic review rejects dense requirement wording.

        Verification Method: verify public function output

        Verification Detail:
        by asserting failed review output names the noun density check.
        """

        result = run_linter_with_review(
            requirement=(
                "A pass artifact with the current source SHA is accepted "
                "as completed agent review."
            ),
            status="fail",
            note=(
                "Noun Density Check: Fail. `current source SHA` stacks more "
                "than two noun modifiers."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Noun Density Check", result.output)

    def test_verification_double_negation_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic review rejects double negation in verification detail.

        Verification Method: verify public function output

        Verification Detail:
        by asserting failed review output names double negation.
        """

        result = run_linter_with_review(
            verification_detail="by checking that `no failure` is false.",
            status="fail",
            note=(
                "Convoluted Wording Check: Fail. `no failure` is false uses "
                "double negation."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("double negation", result.output)
if __name__ == "__main__":
    unittest.main()
