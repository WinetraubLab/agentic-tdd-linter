"""Check the glossary size in one extracted test file."""

from __future__ import annotations

import re

from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord
from .run_conventional_linter import LintIssue


TERM_DEFINITION_PATTERN = re.compile(r"^- `([^`\n]+)`: (\S.*)$")


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


def _file_docstring_terms(file_docstring: str) -> set[str]:
    lines = file_docstring.splitlines()
    try:
        terms_start = next(
            index for index, line in enumerate(lines) if line.strip() == "Terms:"
        )
    except StopIteration:
        return set()

    terms: set[str] = set()
    for line in lines[terms_start + 1 :]:
        text = line.strip()
        if not text:
            continue
        match = TERM_DEFINITION_PATTERN.fullmatch(text)
        if match is None:
            break
        terms.add(match.group(1))
    return terms
