from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class AssertionClarifyTests(unittest.TestCase):
    def test_extra_assertion_fails_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Extra result assertions fail when they prove behavior outside the requirement.

        Verification Method: verify public function output

        Verification Detail:
        Output includes Assertion Purpose Check.
        """

        source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Adding positive numbers returns a positive result.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                a = 1
                b = 2
                c = add_2_positive_numbers(a, b)
                assert c > 0
                assert c == a + b
        '''

        status, reason = linter_e2e_review(
            test_source_code=source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Assertion Purpose Check", reason)

    def test_tagged_input_assertions_pass(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agentic review accepts input assertions marked with `# Input check`.

        Verification Method: verify public function output

        Verification Detail:
        Linter accepts tagged input assertions. Example: positive argument checks use `# Input check`.
        """

        source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Adding positive numbers returns a positive result.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                a = 1
                b = 2
                c = add_2_positive_numbers(a, b)
                assert a > 0  # Input check
                assert b > 0  # Input check
                assert c > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=source,
        )
        self.assertIs(True, status)

    def test_untagged_input_assertions_fail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Missing tags hide validation assertions. Example: positive argument checks need `# Input check`.

        Verification Method: verify public function output

        Verification Detail:
        Linter report cites missing `# Input check` tags.
        """

        source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Adding positive numbers returns a positive result.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                a = 1
                b = 2
                c = add_2_positive_numbers(a, b)
                assert a > 0
                assert b > 0
                assert c > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("# Input check", reason)

if __name__ == "__main__":
    unittest.main()
