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

    def test_generic_requirement_rejects_phrases(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `Generic Requirement` checks reject repeated or swappable phrases.
        Examples include repeated-parser wording and swappable-sentence wording.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes Generic Requirement.
        """

        generic_requirement_sources = (
            # Problem sentence: the same requirement appears on two different tests.
            '''
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
            ''',
            # Problem sentence: "Reject bad sentence structure." is way too generic.
            '''
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
            ''',
        )
        for source in generic_requirement_sources:
            status, reason = linter_e2e_review(
                test_source_code=source,
            )
            self.assertIs(False, status)
            self.assertIn("agent_review_failed", reason)
            self.assertIn("Generic Requirement", reason)

    def test_requirement_scenario_rejects_missing_examples(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Requirement scenario checks reject requirements without examples.
        Examples include missing-file context and unused-template context.

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
        self.assertIn("scenario", reason)

        # Problem sentence: the behavior is stated, but the requirement does
        # not name the template/context scenario that makes it reviewable.
        status, reason = linter_e2e_review(
            test_source_code='''
                def test_rejects_unused_context_variable() -> None:
                    """Test Path: failure path

                    Requirement Tested:
                    Jinja manifest rendering rejects context variables unused by the source template.

                    Verification Method: verify public function output

                    Verification Detail:
                    Error report names unused context variable.
                    """

                    source_template = "Hello {{ name }}"
                    manifest_context = {"name": "Ada", "unused_title": "Dr"}
                    errors = validate_manifest_render(source_template, manifest_context)

                    assert "unused_title" in errors
            ''',
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("scenario", reason)

    def test_requirement_terms_require_owners(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Requirement wording checks reject ambiguous data-flow terms.
        Examples fail when `input`, `output`, `returns`, and `provided` lack owners.

        Verification Method: verify public function output

        Verification Detail:
        Linter report includes ambiguous term guidance.
        """

        # Problem sentence: "input" has no named owner.
        input_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                The input is normalized before validation.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=input_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("input", reason)

        # Problem sentence: "output" has no named owner.
        output_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                The output includes the normalized value.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=output_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("output", reason)

        # Problem sentence: "returns" has no named owner.
        returns_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                The parser returns the expected value.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=returns_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("returns", reason)

        # Problem sentence: "provided" does not name who provides the activity name.
        provided_term_source = '''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                Add an artifact row from a template using the provided activity name.

                Verification Method: verify public function output

                Verification Detail:
                The result is positive.
                """

                assert 1 + 1 > 0
        '''

        status, reason = linter_e2e_review(
            test_source_code=provided_term_source,
        )
        self.assertIs(False, status)
        self.assertIn("agent_review_failed", reason)
        self.assertIn("ambiguous", reason)
        self.assertIn("provided", reason)


if __name__ == "__main__":
    unittest.main()
