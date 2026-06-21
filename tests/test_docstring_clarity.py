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
        Reviewed artifact permits successful check.
        """

        result = run_linter_with_review(
            status="pass",
            note="Sentence Structure Check: Pass.",
        )

        self.assertEqual(0, result.exit_code)

    def test_requirement_long_subject_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects long subjects.

        Verification Method: verify public function output

        Verification Detail:
        Linter report identifies long subject.
        """

        result = run_linter_with_review(
            requirement="The current source artifact emits warning.",
            status="fail",
            note=(
                "Sentence Structure Check: Fail. Requirement uses a long "
                "subject before the main verb."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Sentence Structure Check", result.output)
        self.assertIn("long subject", result.output)

    def test_verification_double_negation_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects double negation in verification details.

        Verification Method: verify public function output

        Verification Detail:
        Linter report identifies double negation.
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

    def test_requirement_five_sentences_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects long requirements.

        Verification Method: verify public function output

        Verification Detail:
        Output includes Sentence Checks.
        """

        requirement = (
            "Parser accepts positive numbers safely. "
            "It adds paired inputs together. "
            "It returns a numeric total. "
            "It preserves sign information for callers. "
            "It gives successful calculation results without extra side effects "
            "or hidden fallback behavior in the result during normal use."
        )

        result = run_linter_with_review(
            requirement=requirement,
            status="fail",
            note="Sentence Checks: Fail. Requirement uses five sentences and forty words.",
        )

        self.assertEqual(40, _word_count(requirement))
        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Sentence Checks", result.output)

    def test_requirement_relative_clause_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Relative clauses reduce clarity. For example `a no longer matches` - matches to what?

        Verification Method: verify public function output

        Verification Detail:
        Output includes `Relative Clause Check`.
        """

        result = run_linter_with_review(
            requirement=(
                "The check command regenerates artifacts whose SHA no longer matches."
            ),
            status="fail",
            note=(
                "Relative Clause Check: Fail. `whose SHA no longer matches` "
                "requires the reader to infer whether SHA refers to artifact "
                "SHA or source SHA."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Relative Clause Check", result.output)
        self.assertIn("whose SHA no longer matches", result.output)

    def test_requirement_named_phrases(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Named phrases clarify local jargon.

        Verification Method: verify public function output

        Verification Detail:
        Linter distinguishes marked and unmarked phrases.
        """

        cases = [
            (
                "prose jargon",
                (
                    "Fishfood exit code matches pass or fail status values in "
                    "agent review artifacts."
                ),
                "fail",
                (
                    "Convoluted Wording Check: Fail. `agent review artifacts` is "
                    "unexplained test-specific jargon in prose; use a named phrase "
                    "such as `agent_review_artifact`."
                ),
                ("agent_review_failed", "test-specific jargon"),
            ),
            (
                "unmarked phrase",
                (
                    "Review markdown includes generic requirement, jargon, "
                    "assertion, and level checks."
                ),
                "fail",
                (
                    "Convoluted Wording Check: Fail. `Review markdown` is a "
                    "test-specific term, so mark it as a backticked named phrase."
                ),
                ("agent_review_failed", "Review markdown", "backticked named phrase"),
            ),
            (
                "backticked phrase",
                (
                    "`Review markdown` includes generic requirement, jargon, "
                    "assertion, and level checks."
                ),
                "pass",
                (
                    "Convoluted Wording Check: Pass. `Review markdown` is a "
                    "backticked named phrase."
                ),
                (),
            ),
            (
                "defined phrase",
                (
                    "Linter exit code matches pass or fail status values in "
                    "`agent_review_artifact`."
                ),
                "pass",
                (
                    "Convoluted Wording Check: Pass. `agent_review_artifact` is "
                    "a named phrase."
                ),
                (),
            ),
        ]

        for label, requirement, status, note, expected_texts in cases:
            with self.subTest(label=label):
                result = run_linter_with_review(
                    requirement=requirement,
                    status=status,
                    note=note,
                )

                expected_exit_code = 1 if status == "fail" else 0
                self.assertEqual(expected_exit_code, result.exit_code)
                for expected_text in expected_texts:
                    self.assertIn(expected_text, result.output)

    def test_verification_structure_fails(self) -> None:
        """Test Path: failure path
    def test_verification_noun_capable_verbs_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects noun-capable main verbs.

        Verification Method: verify public function output

        Verification Detail:
        Linter report identifies noun-capable verbs.
        """

        cases = [
            (
                "names",
                "Output names double negation.",
                (
                    "Sentence Checks: Fail. Sentence Structure Check: Fail. "
                    "`names` is ambiguous between a noun and a verb."
                ),
            ),
            (
                "reports",
                "A pending artifact reports that agent review has not completed.",
                (
                    "Sentence Checks: Fail. Sentence Structure Check: Fail. "
                    "`reports` is commonly used as a noun, even though this "
                    "sentence is grammatically parseable."
                ),
            ),
        ]

        for label, verification_detail, note in cases:
            with self.subTest(label=label):
                result = run_linter_with_review(
                    verification_detail=verification_detail,
                    status="fail",
                    note=note,
                )

                self.assertEqual(1, result.exit_code)
                self.assertIn("agent_review_failed", result.output)
                self.assertIn(label, result.output)
                self.assertIn("Sentence Structure Check", result.output)

if __name__ == "__main__":
    unittest.main()
