"""Render one agent Markdown packet for cross-test review."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path
import re
from typing import Sequence

from jinja2 import Environment, StrictUndefined, Template

from ..indexing_test_functions.extract_tests_from_file import extract_tests_from_file


_TEMPLATE_PATH = "agentic_linter/test_relationship_review.agent.md.j2"
_DEFAULT_ARTIFACT_ROOT = Path("tests") / "agentic_review_artifacts"
_ARTIFACT_NAME = "cross_test_review.agent.md"
_SCORECARD_HEADING = "\n## Review Scorecard\n"
_PAIR_CLASSIFICATION_ROW_PATTERN = re.compile(
    r"^(\|\s*`[^`]+`\s*\|\s*`[^`]+`\s*\|)\s*"
    r"(?:pending|yes|no)\s*\|[^|]*\|$",
    re.MULTILINE,
)


def render_cross_test_agent_md_file(
    test_file_paths: Sequence[Path],
    repo_root: Path,
    artifact_root: Path | None = None,
) -> Path:
    """Write one review packet for relationships among listed test files."""

    root = Path(repo_root).resolve()
    review_root = (
        Path(artifact_root)
        if artifact_root is not None
        else _DEFAULT_ARTIFACT_ROOT
    )
    if not review_root.is_absolute():
        review_root = root / review_root
    artifact_path = review_root / _ARTIFACT_NAME
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        _render_cross_test_agent_md(test_file_paths, root),
        encoding="utf-8",
    )
    return artifact_path


def cross_test_agent_md_file_is_stale(
    test_file_paths: Sequence[Path],
    repo_root: Path,
    artifact_root: Path | None = None,
) -> bool:
    """Return whether embedded criteria or test docstrings differ from current input."""

    root = Path(repo_root).resolve()
    review_root = Path(artifact_root) if artifact_root is not None else _DEFAULT_ARTIFACT_ROOT
    if not review_root.is_absolute():
        review_root = root / review_root
    artifact_path = review_root / _ARTIFACT_NAME
    if not artifact_path.exists():
        return True
    current_scope = _relationship_review_input_scope(
        artifact_path.read_text(encoding="utf-8")
    )
    expected_scope = _relationship_review_input_scope(
        _render_cross_test_agent_md(test_file_paths, root)
    )
    return current_scope != expected_scope


def _render_cross_test_agent_md(
    test_file_paths: Sequence[Path],
    repo_root: Path,
) -> str:
    scope = _build_cross_test_review_scope(test_file_paths, repo_root)
    test_docstrings = [
        (
            f"{test.path.as_posix()}::{test.name}",
            test.docstring or "<missing test docstring>",
        )
        for relative_path in scope
        for test in extract_tests_from_file(repo_root / relative_path, repo_root)
    ]
    return _render_test_relationship_docstrings_agent_md(test_docstrings)


def _render_test_relationship_docstrings_agent_md(
    test_docstrings: Sequence[tuple[str, str]],
) -> str:
    """Render one test-relationship packet containing identifiers and docstrings."""

    tests = [
        {
            "identifier": identifier,
            "docstring": docstring,
        }
        for identifier, docstring in test_docstrings
    ]
    test_pairs = [
        {
            "first_identifier": first["identifier"],
            "second_identifier": second["identifier"],
        }
        for index, first in enumerate(tests)
        for second in tests[index + 1 :]
    ]
    return (
        _test_relationship_review_template()
        .render(tests=tests, test_pairs=test_pairs)
        .rstrip()
        + "\n"
    )


def _relationship_review_input_scope(text: str) -> str:
    """Return criteria and docstrings without editable review results."""

    scope = text.partition(_SCORECARD_HEADING)[0]
    return _PAIR_CLASSIFICATION_ROW_PATTERN.sub(
        r"\1 pending | Replace with overlap evidence. |",
        scope,
    )


def _build_cross_test_review_scope(
    test_file_paths: Sequence[Path],
    repo_root: Path,
) -> list[str]:
    """Return unique repository-relative test paths in input order."""

    repo_root = Path(repo_root).resolve()
    scope: list[str] = []
    seen: set[Path] = set()
    for supplied_path in test_file_paths:
        absolute_path = Path(supplied_path)
        if not absolute_path.is_absolute():
            absolute_path = repo_root / absolute_path
        absolute_path = absolute_path.resolve()
        try:
            relative_path = absolute_path.relative_to(repo_root)
        except ValueError as error:
            raise ValueError(
                f"cross-test review path is outside the repository: {supplied_path}"
            ) from error
        if not absolute_path.is_file():
            raise ValueError(f"cross-test review file does not exist: {relative_path}")
        if relative_path in seen:
            continue
        seen.add(relative_path)
        scope.append(relative_path.as_posix())
    if not scope:
        raise ValueError("cross-test review requires at least one test file")
    return scope


@lru_cache(maxsize=1)
def _test_relationship_review_template() -> Template:
    template_source = files("agentic_tdd_linter").joinpath(_TEMPLATE_PATH).read_text(
        encoding="utf-8"
    )
    environment = Environment(
        autoescape=False,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    return environment.from_string(template_source)
