"""Structured test-docstring checks.

The full test philosophy and docstring contract live in docs/test-philosophy.md.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SKIPPED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".claude",
    ".codex",
    "node_modules",
    "fixtures",
    "helpers",
    "cli_fixtures",
}

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


@dataclass(frozen=True)
class TestFunction:
    """A parsed test function and its structured docstring."""

    path: Path
    name: str
    line: int
    node: ast.FunctionDef | ast.AsyncFunctionDef
    docstring: str


def lint_test_files(paths: Iterable[Path], repo_root: Path) -> list[LintIssue]:
    """Return issues for the provided test files."""

    issues: list[LintIssue] = []
    for path in sorted({Path(path).resolve() for path in paths}):
        issues.extend(lint_test_file(path, repo_root))
    return issues


def lint_test_file(path: Path, repo_root: Path) -> list[LintIssue]:
    """Return issues for a single test file."""

    absolute_path = Path(path).resolve()
    relative_path = _relative_path(absolute_path, repo_root)

    try:
        source = absolute_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(absolute_path))
    except (OSError, SyntaxError) as error:
        return [
            LintIssue(
                path=relative_path,
                test_name="<module>",
                line=1,
                rule="parse_error",
                message=f"could not parse test file: {error}",
            )
        ]

    issues: list[LintIssue] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        test_function = TestFunction(
            path=relative_path,
            name=node.name,
            line=node.lineno,
            node=node,
            docstring=ast.get_docstring(node) or "",
        )
        issues.extend(_lint_test_function(test_function))
    return issues


def all_test_files(repo_root: Path) -> list[Path]:
    """Return all project test files under the repository root."""

    root = Path(repo_root).resolve()
    return sorted(
        path
        for path in root.rglob("*.py")
        if _is_project_test_file(path, root, skip_path_parts=True)
    )


def changed_test_files(repo_root: Path) -> list[Path]:
    """Return changed project test files under the repository root."""

    root = Path(repo_root).resolve()
    changed_values = _git_path_values(root, ["diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"])
    changed_values.extend(_git_path_values(root, ["ls-files", "--others", "--exclude-standard"]))

    changed_paths: list[Path] = []
    for path_value in changed_values:
        path = (root / path_value).resolve()
        if path.is_file() and path.is_relative_to(root):
            if _is_project_test_file(path, root, skip_path_parts=True):
                changed_paths.append(path)
    return sorted(set(changed_paths))


def requested_test_files(paths: Iterable[str], repo_root: Path) -> list[Path]:
    """Resolve explicitly requested test files or directories."""

    root = Path(repo_root).resolve()
    requested: list[Path] = []
    for path_value in paths:
        path = Path(path_value)
        if not path.is_absolute():
            path = root / path
        path = path.resolve()

        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if not path.is_relative_to(root):
            raise ValueError(f"path is outside repository: {path}")
        if path.is_dir():
            requested.extend(
                child
                for child in sorted(path.rglob("*.py"))
                if _is_project_test_file(child, root, skip_path_parts=False)
            )
            continue
        if path.suffix != ".py":
            raise ValueError(f"path is not a Python file: {path}")
        requested.append(path)

    return sorted(set(requested))


def _lint_test_function(test_function: TestFunction) -> list[LintIssue]:
    issues: list[LintIssue] = []

    if not test_function.docstring:
        return [
            _issue(
                test_function,
                "missing_docstring",
                "test function must include a structured docstring",
            )
        ]

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

    if test_function.name.count("_") > 5:
        issues.append(
            _issue(
                test_function,
                "test_name_too_long",
                "test name must be `test_` plus at most five descriptive words",
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

    if verification == "verify private function output" and not _calls_leading_underscore_callable(test_function.node):
        issues.append(
            _issue(
                test_function,
                "private_verification_missing_private_call",
                "private verification must call a leading-underscore callable",
            )
        )

    if verification != "visual inspection by user" and not _has_meaningful_assertion(test_function.node):
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
        if not _calls_named_callable(test_function.node, "write_visual_inspection_artifact"):
            issues.append(
                _issue(
                    test_function,
                    "missing_visual_inspection_helper",
                    "visual inspection tests must call write_visual_inspection_artifact",
                )
            )

    if _uses_mocking(test_function.node):
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


def _issue(test_function: TestFunction, rule: str, message: str) -> LintIssue:
    return LintIssue(
        path=test_function.path,
        test_name=test_function.name,
        line=test_function.line,
        rule=rule,
        message=message,
    )


def _git_path_values(repo_root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_project_test_file(path: Path, repo_root: Path, *, skip_path_parts: bool) -> bool:
    if path.suffix != ".py":
        return False
    try:
        relative_parts = path.resolve().relative_to(repo_root.resolve()).parts
    except ValueError:
        relative_parts = path.parts
    if skip_path_parts and any(part in SKIPPED_PATH_PARTS for part in relative_parts):
        return False
    if path.name.startswith("test_") or path.name.endswith("_tests.py"):
        return True
    return "tests" in relative_parts


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(Path(repo_root).resolve())
    except ValueError:
        return path


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


def _calls_leading_underscore_callable(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        function = child.func
        if isinstance(function, ast.Name) and function.id.startswith("_"):
            return True
        if isinstance(function, ast.Attribute) and function.attr.startswith("_"):
            return True
    return False


def _calls_named_callable(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        function = child.func
        if isinstance(function, ast.Name) and function.id == name:
            return True
        if isinstance(function, ast.Attribute) and function.attr == name:
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
        if call_name == "raises":
            return True
        if call_name.startswith("assert"):
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
