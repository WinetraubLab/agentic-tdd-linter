from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class SelfContainedValueTests(unittest.TestCase):
    def test_external_expected_value_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Expected values require local definitions. Shared constants hide checked values.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Keep Assertions Self-Contained.
        """

        # Problem statement: `EXPECTED_VALUE` supplies the expected result
        # from outside the test body.
        expected_value_source = '''
            def test_expected_value() -> None:
                """Test Path: failure path

                Requirement Tested:
                Function `fun_a` returns the expected value for ten.

                Verification Method: verify public function output

                Verification Detail:
                Linter report includes Keep Assertions Self-Contained.
                """

                expected_value = EXPECTED_VALUE
                assert(fun_a(10), expected_value)
        '''

        status, reason = linter_e2e_review(
            test_source_code=expected_value_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Keep Assertions Self-Contained", reason)

    def test_external_argument_value_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Function argument values require local definitions.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Keep Assertions Self-Contained.
        """

        # Problem statement: `EXPECTED_VALUE` supplies the function argument
        # from outside the test body.
        argument_value_source = '''
            def test_argument_value() -> None:
                """Test Path: failure path

                Requirement Tested:
                Function `fun_a` returns ten for the provided value.

                Verification Method: verify public function output

                Verification Detail:
                Linter report includes Keep Assertions Self-Contained.
                """

                assert(fun_a(EXPECTED_VALUE), 10)
        '''

        status, reason = linter_e2e_review(
            test_source_code=argument_value_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Keep Assertions Self-Contained", reason)

    def test_imported_fact_list_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Imported fact names require local definitions.

        Verification Method: verify public function output

        Verification Detail:
        Review note names `ARTIFACT_BACKED_FACTS` as outside the test body.
        """

        # Problem statement: `ARTIFACT_BACKED_FACTS` supplies the loop inputs
        # from outside the test body.
        imported_fact_list_source = '''
            from ice_cream_database import ARTIFACT_BACKED_FACTS


            def test_artifact_backed_facts_cannot_update_directly() -> None:
                """Test Path: failure path

                Requirement Tested:
                Reject direct updates for facts whose source of truth is another database.

                Verification Method: verify public function output

                Verification Detail:
                Loop checks artifact-backed facts return update rejection errors.
                """

                for fact_name in ARTIFACT_BACKED_FACTS:
                    error = direct_fact_update_error(fact_name)

                    self.assertIn("artifact_db_update", error)
        '''

        status, reason = linter_e2e_review(
            test_source_code=imported_fact_list_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Keep Assertions Self-Contained", reason)
        self.assertIn("ARTIFACT_BACKED_FACTS", reason)

    def test_external_requirement_value_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Requirement values require local definitions.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Keep Assertions Self-Contained.
        """

        # Problem statement: `_five_sentence_requirement` supplies the reviewed
        # requirement from outside the test body.
        requirement_helper_source = '''
            def test_long_requirement_fails() -> None:
                """Test Path: failure path

                Requirement Tested:
                Linter rejects long requirements.

                Verification Method: verify public function output

                Verification Detail:
                Linter report includes Sentence Checks.
                """

                requirement = _five_sentence_requirement()
                result = check_requirement(requirement=requirement)

                assert result.exit_code == 1


            def _five_sentence_requirement() -> str:
                return "Parser accepts positive numbers safely."
        '''

        status, reason = linter_e2e_review(
            test_source_code=requirement_helper_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("outside the test body", reason)


if __name__ == "__main__":
    unittest.main()
