"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for validating backticked requirement-term definitions.

Terms:
- `undefined_requirement_term`: This rule reports a backticked requirement term missing from the file glossary. For example, using an undefined term produces this rule.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentic_tdd_linter.conventional_linter.run_conventional_linter import (
    run_conventional_linter,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)

from tests.conventional_linter.test_harness.requirement_term_definitions import (
    _lint_requirement_term_source,
)


class RequirementTermDefinitionTests(unittest.TestCase):
    def test_accepts_defined_requirement_term(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts a backticked requirement term when the file glossary defines that term.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The `manifest proof` term satisfies glossary-definition validation.
        """

        rules = _lint_requirement_term_source(
            file_docstring="""Verify manifest behavior.

            Terms:
            - `manifest proof`: A stored agent-review result for one source hash.
            """,
            requirement="""`manifest proof` records reviews.
            When reviews pass, `manifest proof` records approval.""",
        )

        self.assertNotIn("undefined_requirement_term", rules)

    def test_reports_undefined_requirement_term(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits undefined_requirement_term when a backticked requirement term is missing from the file glossary.
        Specialized usage: The requirement contains a backticked term with no glossary definition, so conventional linter emits undefined_requirement_term.

        Verification Method: verify private function output

        Verification Detail:
        The `_lint_requirement_term_source` output contains `undefined_requirement_term`.
        """

        rules = _lint_requirement_term_source(
            file_docstring="Verify manifest behavior.",
            requirement="""Manifests record reviews.
            When reviews pass, `manifest proof` records approval.""",
        )

        self.assertIn("undefined_requirement_term", rules)

    def test_requires_colon_definition_format(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits `undefined_requirement_term` when a file glossary definition lacks a colon separator.
        Specialized usage: When a definition has a hyphen separator instead of a colon separator, `conventional_linter` emits `undefined_requirement_term`.

        Verification Method: verify private function output

        Verification Detail:
        The `_lint_requirement_term_source` output contains `undefined_requirement_term`.
        """

        rules = _lint_requirement_term_source(
            file_docstring="""Verify manifest behavior.

            Terms:
            - `manifest proof` - A stored agent-review result.
            """,
            requirement="""`manifest proof` records reviews.
            When reviews pass, `manifest proof` records approval.""",
        )

        self.assertIn("undefined_requirement_term", rules)


if __name__ == "__main__":
    unittest.main()
