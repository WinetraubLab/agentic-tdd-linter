"""Build sources for requirement-term definition tests."""

from __future__ import annotations

import tempfile
import textwrap
from pathlib import Path

from agentic_tdd_linter.conventional_linter.run_conventional_linter import (
    run_conventional_linter,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)


def _lint_requirement_term_source(*, file_docstring: str, requirement: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        normalized_file_docstring = textwrap.dedent(file_docstring).strip()
        normalized_requirement = textwrap.dedent(requirement).strip()
        function_docstring = textwrap.indent(
            "\n".join(
                (
                    '"""Test Path: happy path',
                    "",
                    "Requirement Tested:",
                    normalized_requirement,
                    "",
                    "Verification Method: verify public function output",
                    "",
                    "Verification Detail:",
                    "The manifest contains one review.",
                    '"""',
                )
            ),
            "    ",
        )
        test_file.write_text(
            (
                f'"""{normalized_file_docstring}"""\n\n'
                "def test_manifest() -> None:\n"
                f"{function_docstring}\n\n"
                "    assert True\n"
            ),
            encoding="utf-8",
        )
        test = extract_tests_from_file(test_file, repo_root)[0]
        return {issue.rule for issue in run_conventional_linter(test)}
