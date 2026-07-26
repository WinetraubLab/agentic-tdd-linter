"""Validate the shared module contract declared by one test file."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord
from .run_conventional_linter import (
    LintIssue,
    TEST_MODULE_DECLARATION_PATTERN,
    _field_block_value,
)


def check_test_module_contract(
    tests: Sequence[ExtractedTestRecord],
    repo_root: Path,
) -> list[LintIssue]:
    """Return conventional issues for one test file's module declaration."""

    if not tests:
        return []

    file_docstring = tests[0].file_docstring or ""
    if not file_docstring.strip():
        return [
            _file_issue(
                tests[0],
                "missing_file_docstring",
                (
                    "test file must begin with file-level documentation that "
                    "declares the module it validates"
                ),
            )
        ]

    lines = [line.strip() for line in file_docstring.splitlines() if line.strip()]
    declaration = (
        TEST_MODULE_DECLARATION_PATTERN.fullmatch(lines[0])
        if lines
        else None
    )
    if declaration is None or len(lines) < 2:
        return [
            _file_issue(
                tests[0],
                "invalid_test_module_declaration",
                (
                    "file documentation must begin with "
                    "`Tests in this file validate <module> located at <path>.` "
                    "and `<module> is responsible for <responsibility>.`"
                ),
            )
        ]

    module_name = declaration.group("module")
    responsibility_prefix = f"`{module_name}` is responsible for "
    if (
        not lines[1].startswith(responsibility_prefix)
        or lines[1] == responsibility_prefix
        or not lines[1].endswith(".")
    ):
        return [
            _file_issue(
                tests[0],
                "invalid_test_module_declaration",
                (
                    "the second file-documentation sentence must name "
                    f"`{module_name}` and state its responsibility"
                ),
            )
        ]

    issues: list[LintIssue] = []
    declared_path = Path(declaration.group("path"))
    absolute_path = (Path(repo_root).resolve() / declared_path).resolve()
    if (
        declared_path.is_absolute()
        or ".." in declared_path.parts
        or not absolute_path.is_relative_to(Path(repo_root).resolve())
        or not absolute_path.is_file()
    ):
        issues.append(
            _file_issue(
                tests[0],
                "missing_test_module",
                (
                    f"declared module `{module_name}` must identify an existing "
                    "repository-relative file"
                ),
            )
        )

    required_prefix = f"`{module_name}`"
    for test in tests:
        requirement = _field_block_value(test.docstring, "Requirement Tested")
        if not requirement:
            continue
        first_sentence = requirement.splitlines()[0].strip()
        if first_sentence.startswith(required_prefix):
            continue
        actual_module = _leading_term(first_sentence)
        actual_description = (
            f"`{actual_module}`" if actual_module else "a different subject"
        )
        issues.append(
            LintIssue(
                path=test.path,
                test_name=test.name,
                line=test.line,
                rule="multiple_modules_in_test_file",
                message=(
                    f"test file declares `{module_name}`, but this requirement names "
                    f"{actual_description}; split this test file so each file "
                    "validates one module"
                ),
            )
        )
    return issues


def _leading_term(text: str) -> str:
    if not text.startswith("`"):
        return ""
    closing_tick = text.find("`", 1)
    return text[1:closing_tick] if closing_tick > 1 else ""


def _file_issue(
    test: ExtractedTestRecord,
    rule: str,
    message: str,
) -> LintIssue:
    return LintIssue(
        path=test.path,
        test_name="<module>",
        line=1,
        rule=rule,
        message=message,
    )
