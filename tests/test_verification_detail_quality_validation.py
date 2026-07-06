from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class VerificationDetailQualityValidationTests(unittest.TestCase):
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

    def test_verification_terms_require_owners(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Verification wording checks reject ambiguous data-flow terms.
        The linter fails when `Output` lacks an owner.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes ambiguous data-flow guidance.
        """

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


if __name__ == "__main__":
    unittest.main()
