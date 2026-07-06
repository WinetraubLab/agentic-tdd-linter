from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import linter_e2e_review


class RequirementQualityTests(unittest.TestCase):
    def test_requirement_behavior_rejects_mechanics(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Requirement behavior checks reject mechanics-only requirements.
        The linter fails when requirements name tests, assertions, constants, or levels instead of behavior.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes too-narrow behavior guidance.
        """

        # Problem sentence: requirement names test functions instead of behavior.
        test_names_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `test_normalizes_name` and `test_normalizes_city` fail until each requirement names specific behavior.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=test_names_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names assertion mechanics instead of behavior.
        assertion_mechanics_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Input assertions pass when `assert a > 0` and `assert b > 0` include `# Input check` tags.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=assertion_mechanics_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names `EXPECTED_VALUE` instead of behavior.
        expected_value_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `EXPECTED_VALUE` fails when it supplies function input outside the test body.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=expected_value_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names test levels instead of behavior.
        test_level_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `test_sum_public` and `test_sum_private` fail without mutual `see also` references.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=test_level_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

        # Problem sentence: requirement names another test instead of behavior.
        swappable_requirement_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `test_bad_sentence_structure` fails because `test_sentence_has_verb` could use the same requirement.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=swappable_requirement_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("too narrow", reason)
        self.assertIn("behavior-level", reason)

    def test_requirement_scenario_rejects_vague_example(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Requirement scenario checks reject vague requirements.

        Verification Method: verify public function output

        Verification Detail:
        Linter report asks for scenario context.
        """

        # Problem sentence: render manifest failure is too vague without a
        # concrete file example such as `missing-source.md.j2`.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_reports_manifest_missing_source() -> None:
                    """Test Path: failure path

                    Requirement Tested:
                    Jinja render validation reports files named in the render manifest YAML but missing on disk.

                    Verification Method: verify public function output

                    Verification Detail:
                    Validation error names missing source files.
                    """

                    assert 1 + 1 > 0
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("use case or scenario", reason)
