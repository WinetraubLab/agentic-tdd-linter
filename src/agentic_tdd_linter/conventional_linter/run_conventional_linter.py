"""Run deterministic conventional checks for one extracted test record.

The full test philosophy and docstring contract live in docs/test-philosophy.md.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord


ALLOWED_VERIFICATION_METHODS = (
    "verify public function output",
    "verify private function output",
    "visual inspection by user",
)

ALLOWED_TEST_PATHS = (
    "happy path",
    "failure path",
)

KNOWN_FIELDS = (
    "Test Path",
    "Requirement Tested",
    "Verification Method",
    "Verification Detail",
    "Inspection Instructions",
)

GENERIC_DOCSTRING_RULES = (
    {
        "name": "boilerplate expectation",
        "patterns": (
            r"\bbehaves as expected\b",
            r"\bworks as expected\b",
            r"\bdoes the right thing\b",
        ),
        "message": "split this broad test into smaller tests with specific requirements",
    },
    {
        "name": "multiple behaviors",
        "patterns": (
            r"\b(return|returns|count|counts|check|checks|validate|validates)\b.+,.+,\s*(and|or)\b",
        ),
        "message": "split this test into one returned value, count, or behavior per test",
    },
    {
        "name": "generic action",
        "patterns": (
            r"\bhandles\b",
            r"\bsupports\b.+\band\b",
            r"\bchecks\b.+\band\b",
        ),
        "message": "name the exact behavior, or split the test if it covers multiple behaviors",
    },
    {
        "name": "boilerplate assertion detail",
        "patterns": (
            r"\bby checking the assertions\b",
        ),
        "message": "name the specific output or side effect asserted",
    },
    {
        "name": "vague modal verb",
        "patterns": (
            r"\bcan't\b",
            r"\bcannot\b",
            r"\bcan\b",
            r"\bis able to\b",
        ),
        "message": (
            "state the expected behavior directly, such as accepts, rejects, "
            "returns, raises, preserves, or writes"
        ),
    },
)

DEFAULT_VALUE_MARKERS = (
    r"`[^`]+`",
    r"'[^']+'",
    r'"[^"]+"',
    r"\b\d+\b",
    r"\b[A-Za-z]+_[A-Za-z0-9_]+\b",
)

MOCKING_CALL_NAMES = {
    "AsyncMock",
    "MagicMock",
    "Mock",
    "PropertyMock",
    "create_autospec",
    "mock",
    "mock_open",
    "patch",
}


@dataclass(frozen=True)
class LintIssue:
    """A single linter finding."""

    path: Path
    test_name: str
    line: int
    rule: str
    message: str
    severity: str = "FAIL"


def run_conventional_linter(test_function: ExtractedTestRecord) -> list[LintIssue]:
    """Return conventional-linter issues for one extracted test record."""

    issues: list[LintIssue] = []

    if not test_function.docstring:
        return [
            _issue(
                test_function,
                "missing_docstring",
                "test function must include a structured docstring",
            )
        ]

    if not _field_headers_are_separated(test_function.docstring):
        issues.append(
            _issue(
                test_function,
                "invalid_field_spacing",
                "structured docstring fields must be separated by blank lines",
            )
        )

    test_path = _same_line_field_value(test_function.docstring, "Test Path")
    if not test_path:
        issues.append(_issue(test_function, "missing_test_path", "missing Test Path field"))
    elif test_path not in ALLOWED_TEST_PATHS:
        issues.append(
            _issue(
                test_function,
                "invalid_test_path",
                f"Test Path must be one of {ALLOWED_TEST_PATHS}",
            )
        )

    if _descriptive_name_word_count(test_function.name) > 5:
        issues.append(
            _issue(
                test_function,
                "test_name_too_long",
                "test name must contain at most five descriptive words; "
                "the Python `test_` prefix is not counted",
            )
        )

    requirement = _field_value(test_function.docstring, "Requirement Tested")
    if not requirement:
        issues.append(_issue(test_function, "missing_requirement", "missing Requirement Tested field"))
    elif not _field_is_own_line(test_function.docstring, "Requirement Tested"):
        issues.append(
            _issue(
                test_function,
                "invalid_requirement_format",
                "Requirement Tested must put text on the next line",
            )
        )

    verification = _same_line_field_value(test_function.docstring, "Verification Method")
    if not verification:
        issues.append(_issue(test_function, "missing_verification_method", "missing Verification Method field"))
    elif verification not in ALLOWED_VERIFICATION_METHODS:
        issues.append(
            _issue(
                test_function,
                "invalid_verification_method",
                f"Verification Method must be one of {ALLOWED_VERIFICATION_METHODS}",
            )
        )

    for trouble_match in _docstring_trouble_matches(test_function.docstring):
        issues.append(
            _issue(
                test_function,
                "generic_docstring",
                f"rewrite the docstring to name the specific behavior: {trouble_match}",
            )
        )

    for trouble_match in _requirement_default_trouble_matches(requirement):
        issues.append(
            _issue(
                test_function,
                "implicit_default_value",
                trouble_match,
            )
        )

    if _field_line_exists(test_function.docstring, "Verification Detail"):
        detail = _field_value(test_function.docstring, "Verification Detail")
        if not detail:
            issues.append(
                _issue(test_function, "missing_verification_detail", "missing Verification Detail text")
            )
        elif not _field_is_own_line(test_function.docstring, "Verification Detail"):
            issues.append(
                _issue(
                    test_function,
                    "invalid_verification_detail_format",
                    "Verification Detail must put text on the next line",
                )
            )

    if verification == "verify private function output" and not _test_calls_private_function(test_function):
        issues.append(
            _issue(
                test_function,
                "private_verification_missing_private_call",
                "private verification must call a leading-underscore callable",
            )
        )

    if verification != "visual inspection by user" and not _test_has_meaningful_assertion(test_function):
        issues.append(
            _issue(
                test_function,
                "missing_assertion",
                "test must include an assertion, unittest assertion method, or pytest.raises call",
            )
        )

    if verification == "visual inspection by user":
        detail = _field_value(test_function.docstring, "Verification Detail")
        instructions = _field_value(test_function.docstring, "Inspection Instructions")
        if "tests/artifacts" not in detail or not re.search(r"tests/artifacts/.+\.(png|jpg|jpeg)\b", detail):
            issues.append(
                _issue(
                    test_function,
                    "missing_visual_inspection_artifact",
                    "visual inspection tests must name a PNG or JPG under tests/artifacts",
                )
            )
        if not instructions:
            issues.append(
                _issue(
                    test_function,
                    "missing_inspection_instructions",
                    "visual inspection tests must include Inspection Instructions",
                )
            )
        elif not _field_is_own_line(test_function.docstring, "Inspection Instructions"):
            issues.append(
                _issue(
                    test_function,
                    "invalid_inspection_instructions_format",
                    "Inspection Instructions must put text on the next line",
                )
            )
        if not _test_calls_named_callable(test_function, "write_visual_inspection_artifact"):
            issues.append(
                _issue(
                    test_function,
                    "missing_visual_inspection_helper",
                    "visual inspection tests must call write_visual_inspection_artifact",
                )
            )

    if _test_uses_mocking(test_function):
        detail = _field_value(test_function.docstring, "Verification Detail")
        if "mock" not in detail.lower():
            issues.append(
                _issue(
                    test_function,
                    "mocking_detail_missing",
                    "tests that use mocking must mention mocking in Verification Detail",
                )
            )

    if requirement and len(requirement.split()) > 30:
        issues.append(
            _issue(
                test_function,
                "requirement_too_long",
                "Requirement Tested must be 30 words or fewer",
            )
        )

    return issues


def _issue(test_function: ExtractedTestRecord, rule: str, message: str) -> LintIssue:
    return LintIssue(
        path=test_function.path,
        test_name=test_function.name,
        line=test_function.line,
        rule=rule,
        message=message,
    )


def _field_value(docstring: str, field_name: str) -> str:
    prefix = f"{field_name}:"
    lines = [line.strip() for line in docstring.splitlines()]
    for index, text in enumerate(lines):
        if text == prefix:
            for next_text in lines[index + 1 :]:
                if _is_field_line(next_text):
                    return ""
                if next_text:
                    return next_text
            return ""
        if text.startswith(prefix):
            return text.removeprefix(prefix).strip()
    return ""


def _same_line_field_value(docstring: str, field_name: str) -> str:
    prefix = f"{field_name}:"
    for line in docstring.splitlines():
        text = line.strip()
        if text.startswith(prefix):
            return text.removeprefix(prefix).strip()
    return ""


def _field_line_exists(docstring: str, field_name: str) -> bool:
    prefix = f"{field_name}:"
    return any(line.strip().startswith(prefix) for line in docstring.splitlines())


def _field_is_own_line(docstring: str, field_name: str) -> bool:
    prefix = f"{field_name}:"
    return any(line.strip() == prefix for line in docstring.splitlines())


def _is_field_line(text: str) -> bool:
    return any(text == f"{field}:" or text.startswith(f"{field}:") for field in KNOWN_FIELDS)


def _field_headers_are_separated(docstring: str) -> bool:
    lines = [line.strip() for line in docstring.splitlines()]
    field_indexes = [
        index
        for index, text in enumerate(lines)
        if _is_field_line(text)
    ]
    if not field_indexes:
        return True
    return all(index == field_indexes[0] or lines[index - 1] == "" for index in field_indexes)


def _docstring_trouble_matches(docstring: str) -> list[str]:
    matches: list[str] = []
    for rule in GENERIC_DOCSTRING_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, docstring, flags=re.IGNORECASE):
                matches.append(f"{rule['name']}: {rule['message']}")
                break
    return matches


def _requirement_default_trouble_matches(requirement: str) -> list[str]:
    matches: list[str] = []
    if re.search(r"\bdefault\b", requirement, flags=re.IGNORECASE):
        has_value_marker = any(re.search(pattern, requirement) for pattern in DEFAULT_VALUE_MARKERS)
        if not has_value_marker:
            matches.append(
                "keep `default` only when the requirement also names the exact value being asserted"
            )
    return matches


def _test_calls_private_function(test_function: ExtractedTestRecord) -> bool:
    if test_function.node is not None:
        return _calls_leading_underscore_callable(test_function.node)
    return bool(re.search(r"(?<![\w$])_[A-Za-z][\w$]*\s*\(", test_function.source))


def _descriptive_name_word_count(name: str) -> int:
    descriptive_name = name.removeprefix("test_")
    return len(re.findall(r"[A-Za-z0-9]+", descriptive_name))


def _test_calls_named_callable(test_function: ExtractedTestRecord, name: str) -> bool:
    if test_function.node is not None:
        return _calls_named_callable(test_function.node, name)
    return bool(re.search(rf"(?<![\w$]){re.escape(name)}\s*\(", test_function.source))


def _test_has_meaningful_assertion(test_function: ExtractedTestRecord) -> bool:
    if test_function.node is not None:
        return _has_meaningful_assertion(test_function.node)
    return bool(
        re.search(
            r"(?<![\w$])(?:assert(?:\.[A-Za-z_$][\w$]*)?|expect)\s*\(",
            test_function.source,
        )
    )


def _test_uses_mocking(test_function: ExtractedTestRecord) -> bool:
    if test_function.node is not None:
        return _uses_mocking(test_function.node)
    mocking_patterns = (
        r"(?<![\w$])(?:vi|jest|sinon)\.",
        r"(?<![\w$])(?:mock|spyOn|stub)\s*\(",
    )
    return any(re.search(pattern, test_function.source) for pattern in mocking_patterns)


def _calls_leading_underscore_callable(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return _calls_matching_name(node, lambda name: name.startswith("_"))


def _calls_named_callable(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    return _calls_matching_name(node, lambda call_name: call_name == name)


def _calls_matching_name(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    predicate: Callable[[str], bool],
) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        parts = _call_name_parts(child.func)
        if parts and predicate(parts[-1]):
            return True
    return False


def _uses_mocking(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        targets = []
        if isinstance(child, ast.Call):
            targets.append(child.func)
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            targets.extend(child.decorator_list)
        for target in targets:
            if any(part in MOCKING_CALL_NAMES for part in _call_name_parts(target)):
                return True
    return False


def _has_meaningful_assertion(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if not isinstance(child, ast.Call):
            continue
        parts = _call_name_parts(child.func)
        if not parts:
            continue
        call_name = parts[-1]
        if call_name == "raises" or call_name.startswith("assert"):
            return True
    return False


def _call_name_parts(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return _call_name_parts(node.value) + [node.attr]
    if isinstance(node, ast.Call):
        return _call_name_parts(node.func)
    return []
