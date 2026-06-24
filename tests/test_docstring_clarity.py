from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class DocstringClarityTests(unittest.TestCase):
    def test_clear_docstring_passes_review(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Sentence structure passes for a simple requirement.

        Verification Method: verify public function output

        Verification Detail:
        Reviewed artifact permits successful check.
        """

        # Review reason: simple requirement and detail satisfy the sentence checks.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Adding two numbers must yield positive result.

                    Verification Method: verify public function output

                    Verification Detail:
                    The result is positive.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(True, status)

    def test_long_subjects_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects long subjects.

        Verification Method: verify public function output

        Verification Detail:
        Linter report identifies long subject.
        """

        # Review reason: requirement uses a long subject before the main verb.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    The current source artifact emits warning.

                    Verification Method: verify public function output

                    Verification Detail:
                    The result is positive.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Sentence Structure Check", reason)
        self.assertIn("long subject", reason)

        # Review reason: verification detail uses a long subject before the main verb.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Adding two numbers must yield positive result.

                    Verification Method: verify public function output

                    Verification Detail:
                    The captured failure output names double negation.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Sentence Structure Check", reason)
        self.assertIn("long subject", reason)

    def test_verification_double_negation_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects double negation in verification details.

        Verification Method: verify public function output

        Verification Detail:
        Linter report identifies double negation.
        """

        # Review reason: `no failure` is false uses double negation.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Adding two numbers must yield positive result.

                    Verification Method: verify public function output

                    Verification Detail:
                    by checking that `no failure` is false.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("double negation", reason)

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

        # Review reason: requirement has five sentences and combines too many ideas.
        status, reason = linter_e2e_review(
            test_source_code=f'''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    {requirement}

                    Verification Method: verify public function output

                    Verification Detail:
                    The result is positive.
                    """

                    assert 1 + 1 > 0
            ''',
        )

        self.assertIs(False, status)
        self.assertEqual(40, _word_count(requirement))
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Sentence Checks", reason)

    def test_requirement_relative_clause_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Relative clauses reduce clarity. For example `a no longer matches` - matches to what?

        Verification Method: verify public function output

        Verification Detail:
        Output includes `Relative Clause Check`.
        """

        # Review reason: `whose SHA no longer matches` omits the SHA referent.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    The check command regenerates artifacts whose SHA no longer matches.

                    Verification Method: verify public function output

                    Verification Detail:
                    The result is positive.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Relative Clause Check", reason)
        self.assertIn("whose SHA no longer matches", reason)

    def test_unmarked_requirement_phrases_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Unmarked phrases trigger review failures.

        Verification Method: verify public function output

        Verification Detail:
        Review reason cites two unmarked phrases.
        """

        # Previous case: prose jargon.
        # Problem sentence: "agent review artifacts" is local project jargon,
        # so the phrase needs code quotes or a concrete definition.
        agent_review_artifacts_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Dogfood exit code matches pass or fail status values in agent review artifacts.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=agent_review_artifacts_source,
        )
        self.assertIs(False, status, "`agent review artifacts` should fail")
        self.assertIn("agent_review_failed", reason)
        self.assertIn("test-specific jargon", reason)

        # Previous case: unmarked phrase.
        # Problem sentence: "Review markdown" is a local named phrase,
        # so the phrase needs code quotes.
        review_markdown_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Review markdown includes generic requirement, jargon, assertion, and level checks.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=review_markdown_source,
        )
        self.assertIs(False, status, "`Review markdown` should fail without code quotes")
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Review markdown", reason)
        self.assertIn("backticked named phrase", reason)

        # Previous case: defined phrase without its code quotes.
        # Problem sentence: "agent_review_artifact" is a project named phrase,
        # so the phrase needs code quotes when it appears in prose.
        agent_review_artifact_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Linter exit code matches pass or fail status values in agent_review_artifact.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=agent_review_artifact_source,
        )
        self.assertIs(False, status, "`agent_review_artifact` should fail without code quotes")
        self.assertIn("agent_review_failed", reason)
        self.assertIn("agent_review_artifact", reason)
        self.assertIn("backticked named phrase", reason)

    def test_marked_requirement_phrases_pass(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Code-quoted phrases satisfy phrase rules.

        Verification Method: verify public function output

        Verification Detail:
        Review reason confirms phrase checks.
        """

        # Previous case: backticked phrase.
        review_markdown_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `Review markdown` includes generic requirement, jargon, assertion, and level checks.

                Verification Method: verify public function output


    def test_verification_sentence_structure_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Verification details require Subject -> Verb -> Object.

        Verification Method: verify public function output

        Verification Detail:
        Linter report identifies sentence structure failures.
        """

        cases = [
            (
                "unclear structure",
                "by asserting failed review output names self-contained assertions.",
                (
                    "Sentence Checks: Fail. Sentence Structure Check: Fail. "
                    "`by asserting failed review output names self-contained assertions` "
                    "has no clear Subject -> Verb -> Object structure."
                ),
            ),
            (
                "missing subject",
                (
                    "by changing a reviewed test file and asserting the artifact "
                    "returns to pending."
                ),
                (
                    "Sentence Checks: Fail. Sentence Structure Check: Fail. "
                    "`by changing a reviewed test file and asserting the artifact "
                    "returns to pending` has no Subject -> Verb -> Object structure "
                    "because it has no subject before the main verb."
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
                self.assertIn("Subject -> Verb -> Object", result.output)

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

    def test_verification_five_sentences_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects long verification details.

        Verification Method: verify public function output

        Verification Detail:
        Output includes Sentence Checks.
        """

        verification_detail = (
            "by checking the sum is positive. "
            "It uses two numbers. "
            "It compares a total. "
            "It confirms normal output. "
            "It records the calculation result without hidden fallback checks or "
            "extra branch expectations during review for this ordinary addition "
            "example case only."
        )

        # Review reason: verification detail is too long and combines too many ideas.
        status, reason = linter_e2e_review(
            test_source_code=f'''
                def test_adds_numbers() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Adding two numbers must yield positive result.

                    Verification Method: verify public function output

                    Verification Detail:
                    {verification_detail}
                    """

                    assert 1 + 1 > 0
            ''',
        )

        self.assertIs(False, status)
        self.assertEqual(40, _word_count(verification_detail))
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Sentence Checks", reason)


def _word_count(text: str) -> int:
    return len(text.split())


if __name__ == "__main__":
    unittest.main()
