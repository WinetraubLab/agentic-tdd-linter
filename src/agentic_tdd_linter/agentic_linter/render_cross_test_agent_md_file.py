"""Render one agent Markdown packet for cross-test review."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Sequence

from jinja2 import Environment, StrictUndefined, Template


_TEMPLATE_PATH = "agentic_linter/cross_test_review.agent.md.j2"
_DEFAULT_ARTIFACT_ROOT = Path("tests") / "agentic_review_artifacts"
_ARTIFACT_NAME = "cross_test_review.agent.md"
_SCORECARD_HEADING = "\n## Review Scorecard\n"


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
    """Return whether embedded criteria or test sources differ from current input."""

    root = Path(repo_root).resolve()
    review_root = Path(artifact_root) if artifact_root is not None else _DEFAULT_ARTIFACT_ROOT
    if not review_root.is_absolute():
        review_root = root / review_root
    artifact_path = review_root / _ARTIFACT_NAME
    if not artifact_path.exists():
        return True
    current_scope = artifact_path.read_text(encoding="utf-8").partition(
        _SCORECARD_HEADING
    )[0]
    expected_scope = _render_cross_test_agent_md(test_file_paths, root).partition(
        _SCORECARD_HEADING
    )[0]
    return current_scope != expected_scope


def _render_cross_test_agent_md(
    test_file_paths: Sequence[Path],
    repo_root: Path,
) -> str:
    scope = _build_cross_test_review_scope(test_file_paths, repo_root)
    test_files = [
        {
            "path": relative_path,
            "source": (repo_root / relative_path).read_text(encoding="utf-8"),
        }
        for relative_path in scope
    ]
    return _cross_test_review_template().render(test_files=test_files).rstrip() + "\n"


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
def _cross_test_review_template() -> Template:
    template_source = files("agentic_tdd_linter").joinpath(_TEMPLATE_PATH).read_text(
        encoding="utf-8"
    )
    environment = Environment(
        autoescape=False,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    return environment.from_string(template_source)
