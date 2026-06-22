from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class GenericWordingTests(unittest.TestCase):
    def test_repeated_requirement_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter identifies repeated requirements when they hide test-specific behavior.

        Verification Method: verify public function output

        Verification Detail:
        Output includes Generic Requirement.
        """

        source = '''
            def test_normalizes_name() -> None:
                """Test Path: happy path

                Requirement Tested:
                Parser returns normalized value.

                Verification Method: verify public function output

                Verification Detail:
                The assertion compares a lowercase name.
                """

                assert normalize_name("Ada") == "ada"


            def test_normalizes_city() -> None:
                """Test Path: happy path

                Requirement Tested:
                Parser returns normalized value.

                Verification Method: verify public function output

                Verification Detail:
                The assertion compares a lowercase city.
                """

                assert normalize_city("Paris") == "paris"
        '''

        status, reason = linter_e2e_review(
            test_source_code=source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Generic Requirement", reason)

    def test_swappable_requirement_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Generic requirements fail when they fit multiple tests.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Generic Requirement.
        """

        source = '''
            def test_sentence_has_verb() -> None:
                """Test Path: happy path

                Requirement Tested:
                Sentences should have a verb.

                Verification Method: verify public function output

                Verification Detail:
                The assertion checks a sentence with a verb.
                """

                assert validate_sentence("Apple become a catapiller") == "pass"


            def test_bad_sentence_structure() -> None:
                """Test Path: failure path

                Requirement Tested:
                Reject bad sentence structure.

                Verification Method: verify public function output

                Verification Detail:
                The assertion checks a sentence without a verb.
                """

                assert validate_sentence("Apple catapiller") == "fail"
        '''

        # Review reason: "Reject bad sentence structure." is way too generic.
        status, reason = linter_e2e_review(
            test_source_code=source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Generic Requirement", reason)
        self.assertIn("Reject bad sentence structure", reason)
        self.assertIn("way too generic", reason)


if __name__ == "__main__":
    unittest.main()
