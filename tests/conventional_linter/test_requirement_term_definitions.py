"""Verify requirement-term definition rules."""

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
        Conventional linter accepts backticked terms when file glossaries define them.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Rules exclude `undefined_requirement_term`.
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
        Conventional linter emits issues when file glossaries omit backticked terms.
        Specialized usage: For glossary validation, backticked term is absent instead of defined.

        Verification Method: verify private function output

        Verification Detail:
        Rules contain `undefined_requirement_term`.
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
        Conventional linter prohibits definitions when their separators invoke hyphens.
        Specialized usage: For definition format, separator is a hyphen instead of a colon.

        Verification Method: verify private function output

        Verification Detail:
        Rules contain `undefined_requirement_term`.
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
