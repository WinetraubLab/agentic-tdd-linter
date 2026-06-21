from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import run_linter_source_with_review, run_linter_with_review


class RequirementVerificationFormulationTests(unittest.TestCase):
    def test_narrow_requirement_examples_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Narrow requirements fail when examples replace behavior.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes too-narrow guidance.
        """

        cases = [
            (
                "sample tests",
                (
                    "`test_normalizes_name` and `test_normalizes_city` fail until "
                    "each requirement names specific behavior."
                ),
                (
                    "Requirement Formulation Check: Fail. Requirement is too narrow "
                    "because it names exact sample tests instead of describing the "
                    "behavior-level rule."
                ),
            ),
            (
                "sample assertions",
                (
                    "Input assertions pass when `assert a > 0` and `assert b > 0` "
                    "include `# Input check` tags."
                ),
                (
                    "Requirement Formulation Check: Fail. Requirement is too narrow "
                    "because it quotes exact sample assertions instead of describing "
                    "the behavior-level rule."
                ),
            ),
            (
                "sample constants",
                (
                    "`EXPECTED_VALUE` fails when it supplies function input outside "
                    "the test body."
                ),
                (
                    "Requirement Formulation Check: Fail. Requirement is too narrow "
                    "because it quotes an exact sample constant instead of describing "
                    "the behavior-level rule."
                ),
            ),
            (
                "sample cross references",
                (
                    "`test_sum_public` and `test_sum_private` fail without mutual "
                    "`see also` references."
                ),
                (
                    "Requirement Formulation Check: Fail. Requirement is too narrow "
                    "because it names exact sample tests and the `see also` mechanic "
                    "instead of describing the behavior-level rule."
                ),
            ),
        ]

        for label, requirement, note in cases:
            with self.subTest(label=label):
                result = run_linter_with_review(
                    requirement=requirement,
                    status="fail",
                    note=note,
                )

                self.assertEqual(1, result.exit_code)
                self.assertIn("agent_review_failed", result.output)
                self.assertIn("too narrow", result.output)
                self.assertIn("behavior-level", result.output)

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

