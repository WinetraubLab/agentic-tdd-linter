"""Check the glossary size in one extracted test file."""

from __future__ import annotations

from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord
from .run_conventional_linter import LintIssue, _file_docstring_terms


def check_file_docstring_term_count(
    test_function: ExtractedTestRecord,
) -> list[LintIssue]:
    """Return one issue when a test-file glossary contains more than five terms."""

    term_count = len(_file_docstring_terms(test_function.file_docstring or ""))
    if term_count <= 5:
        return []
    return [
        LintIssue(
            path=test_function.path,
            test_name="<module>",
            line=1,
            rule="too_many_file_docstring_terms",
            message=f"test file must define at most 5 terms; found {term_count}",
        )
    ]
