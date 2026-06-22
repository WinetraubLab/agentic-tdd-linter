from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import run_linter_source_with_review


class TestLevelTests(unittest.TestCase):
    def test_missing_level_reference_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Duplicate test levels require cross references.

        Verification Method: verify public function output

        Verification Detail:
        Output includes Test Level Redundancy Check.
        """

        source = '''
            def test_sum_public() -> None:
                """Test Path: happy path

                Requirement Tested:
                `sum_a_b` returns `5` for inputs `2` and `3`.

                Verification Method: verify public function output

                Verification Detail:
                by asserting public addition returns `5`.
                """

                assert sum_a_b(2, 3) == 5


            def test_sum_private() -> None:
                """Test Path: happy path

                Requirement Tested:
                `_sum_a_b` returns `5` for inputs `2` and `3`.

                Verification Method: verify private function output

                Verification Detail:
                by asserting private helper returns `5`.
                """

                assert _sum_a_b(2, 3) == 5
        '''

        status, reason = linter_e2e_review(
            test_source_code=source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("Test Level Redundancy Check", reason)

    def test_level_reference_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Public and private duplicate tests pass when both requirements include `see also` references.

        Verification Method: verify public function output

        Verification Detail:
        Mutual references permit linter success.
        """

        source = '''
            def test_sum_public() -> None:
                """Test Path: happy path

                Requirement Tested:
                `sum_a_b` returns `5` for inputs `2` and `3`; see also `test_sum_private`, which covers the private level.

                Verification Method: verify public function output

                Verification Detail:
                by asserting public addition returns `5`.
                """

                assert sum_a_b(2, 3) == 5


            def test_sum_private() -> None:
                """Test Path: happy path

                Requirement Tested:
                `_sum_a_b` returns `5` for inputs `2` and `3`; see also `test_sum_public`, which covers the public level.

                Verification Method: verify private function output

                Verification Detail:
                by asserting private helper returns `5`.
                """

                assert _sum_a_b(2, 3) == 5
        '''

        result = run_linter_source_with_review(
            source=source,
            status="pass",
            note="Test Level Redundancy Check: Pass.",
        )

        self.assertEqual(0, result.exit_code)


if __name__ == "__main__":
    unittest.main()
