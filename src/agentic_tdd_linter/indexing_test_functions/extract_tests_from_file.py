"""Choose the language-specific extractor for one test file."""

from __future__ import annotations

from pathlib import Path

from .extract_python_tests_from_file import extract_python_tests_from_file
from .extract_typescript_tests_from_file import extract_typescript_tests_from_file
from .extracted_test_record import ExtractedTestRecord


def extract_tests_from_file(path: Path, repo_root: Path) -> list[ExtractedTestRecord]:
    """Extract tests using the implementation for the file's language."""

    absolute_path = Path(path).resolve()
    if absolute_path.name.endswith(".test.ts"):
        return extract_typescript_tests_from_file(absolute_path, repo_root)
    if absolute_path.suffix == ".py":
        return extract_python_tests_from_file(absolute_path, repo_root)
    raise ValueError(f"unsupported test file: {absolute_path}")
