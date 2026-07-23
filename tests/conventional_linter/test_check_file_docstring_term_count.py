"""Conventional-linter tests verify deterministic test-file glossary limits.

Terms:
- `glossary limit`: The glossary limit permits no more than five defined terms. For example, six terms produce a lint issue.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agentic_tdd_linter.conventional_linter.check_file_docstring_term_count import (
    check_file_docstring_term_count,
)
from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)


class FileDocstringTermCountTests(unittest.TestCase):
    def test_reports_excess_term_rule(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Conventional linter emits too_many_file_docstring_terms above `glossary limit`.
        Specialized usage: For glossary limits, term count exceeds `glossary limit` instead of staying within it, so conventional linter emits too_many_file_docstring_terms.

        Verification Method: verify public function output

        Verification Detail:
        Issue list contains `too_many_file_docstring_terms`.
        """

        term_names = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta")
        definitions = "\n".join(
            f"- `{term}`: The {term} term has a definition." for term in term_names
        )
        test = ExtractedTestRecord(
            path=Path("tests/test_example.py"),
            name="test_example",
            line=1,
            node=None,
            docstring="",
            file_docstring=f"Verify examples.\n\nTerms:\n{definitions}",
        )

        issues = check_file_docstring_term_count(test)

        self.assertIn("too_many_file_docstring_terms", [issue.rule for issue in issues])
