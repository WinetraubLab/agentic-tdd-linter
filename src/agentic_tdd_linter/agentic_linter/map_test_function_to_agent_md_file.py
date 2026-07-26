"""Map a test function to its persisted agent Markdown file."""

from __future__ import annotations

import re
from pathlib import Path

from ..indexing_test_functions.discover_test_files import discover_test_files
from ..indexing_test_functions.extract_tests_from_file import extract_tests_from_file
from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord


__all__ = [
    "map_agent_md_file_to_test_function",
    "map_test_function_to_agent_md_file",
]


_DEFAULT_AGENT_REVIEW_ARTIFACT_DIR = Path("tests") / "agentic_review_artifacts"


def map_test_function_to_agent_md_file(
    test_file_path: Path,
    repo_root: Path,
    artifact_root: Path | None = None,
    test_name: str | None = None,
) -> Path:
    """Map one test function to its persisted agent Markdown path."""

    root = Path(repo_root).resolve()
    test_file = Path(test_file_path).resolve()
    review_root = (
        Path(artifact_root)
        if artifact_root is not None
        else _DEFAULT_AGENT_REVIEW_ARTIFACT_DIR
    )
    if not review_root.is_absolute():
        review_root = root / review_root

    suffix = f"__{_test_name_slug(test_name)}" if test_name is not None else ""
    return review_root / f"{test_file.stem}{suffix}.agent.md"


def map_agent_md_file_to_test_function(
    agent_md_file: Path,
    repo_root: Path,
    artifact_root: Path | None = None,
) -> ExtractedTestRecord:
    """Map an agent Markdown path back to its unique test function."""

    root = Path(repo_root).resolve()
    target_path = Path(agent_md_file).resolve()
    matches = [
        test
        for test_file in discover_test_files(root)
        for test in extract_tests_from_file(test_file, root)
        if map_test_function_to_agent_md_file(
            test_file,
            root,
            artifact_root,
            test.name,
        ).resolve()
        == target_path
    ]
    if not matches:
        raise ValueError(
            f"agent Markdown file does not map to a test function: {agent_md_file}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"agent Markdown file maps to multiple test functions: {agent_md_file}"
        )
    return matches[0]


def _test_name_slug(test_name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", test_name).strip("_").lower()
    return slug or "test"
