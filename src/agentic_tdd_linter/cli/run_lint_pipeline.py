"""Coordinate test discovery, linting, and agent-review proof checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from ..agentic_linter.build_manifest_from_agent_md_files import (
    _lint_agent_review_manifest,
    build_manifest_from_agent_md_files,
)
from ..agentic_linter.determine_agent_md_status import (
    _agent_md_file_is_stale,
    _lint_agent_md_file,
)
from ..agentic_linter.map_test_function_to_agent_md_file import (
    map_test_function_to_agent_md_file,
)
from ..agentic_linter.render_agent_md_file import render_agent_md_file
from ..conventional_linter.run_conventional_linter import (
    LintIssue,
    run_conventional_linter,
)
from ..indexing_test_functions.discover_test_files import discover_test_files
from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord
from ..indexing_test_functions.extract_tests_from_file import extract_tests_from_file


@dataclass(frozen=True)
class LintPipelineResult:
    """Files, issues, and optional manifest output produced by one lint run."""

    files: tuple[Path, ...]
    issues: tuple[LintIssue, ...]
    recorded_manifest_path: Path | None = None
    recorded_count: int = 0


def run_lint_pipeline(
    *,
    repo_root: Path,
    test_root: Path = Path("tests"),
    paths: Sequence[str] = (),
    all_files: bool = False,
    review_proof: str = "auto",
    manifest_path: Path | None = None,
    reviewer: str = "",
) -> LintPipelineResult:
    """Run the complete lint workflow and return its structured result."""

    root = Path(repo_root).resolve()
    resolved_test_root = _resolve_test_root(root, test_root)
    artifact_root = resolved_test_root / "agentic_review_artifacts"
    files = _selected_test_files(root, resolved_test_root, paths, all_files)
    tests_by_file, issues = _extract_and_lint_tests(files, root)
    review_files = [test_file for test_file in files if tests_by_file.get(test_file.resolve())]

    recorded_manifest_path: Path | None = None
    recorded_count = 0
    if review_files and review_proof == "manifest":
        issues.extend(
            _lint_agent_review_manifest(
                review_files,
                root,
                manifest_path,
                tests_by_file=tests_by_file,
            )
        )
    elif review_files and review_proof == "artifact":
        _write_missing_or_stale_agent_review_artifacts(
            review_files,
            root,
            artifact_root,
            tests_by_file,
        )
        issues.extend(
            _lint_agent_review_artifacts(
                review_files,
                root,
                artifact_root,
                tests_by_file,
            )
        )
        if not issues:
            recorded_manifest_path, recorded_count, manifest_issues = (
                build_manifest_from_agent_md_files(
                    review_files,
                    root,
                    reviewer=reviewer,
                    manifest_path=manifest_path,
                    artifact_root=artifact_root,
                    tests_by_file=tests_by_file,
                )
            )
            issues.extend(manifest_issues)
            if manifest_issues:
                recorded_manifest_path = None
                recorded_count = 0
    elif review_files and review_proof == "auto":
        manifest_issues = _lint_agent_review_manifest(
            review_files,
            root,
            manifest_path,
            tests_by_file=tests_by_file,
        )
        if manifest_issues:
            _write_missing_or_stale_agent_review_artifacts(
                review_files,
                root,
                artifact_root,
                tests_by_file,
            )
            issues.extend(
                _lint_agent_review_artifacts(
                    review_files,
                    root,
                    artifact_root,
                    tests_by_file,
                )
            )
            if not issues:
                recorded_manifest_path, recorded_count, refresh_issues = (
                    build_manifest_from_agent_md_files(
                        review_files,
                        root,
                        reviewer=reviewer,
                        manifest_path=manifest_path,
                        artifact_root=artifact_root,
                        tests_by_file=tests_by_file,
                    )
                )
                issues.extend(refresh_issues)
                if refresh_issues:
                    recorded_manifest_path = None
                    recorded_count = 0
    elif review_files:
        raise ValueError(f"unsupported review proof source: {review_proof}")

    return LintPipelineResult(
        files=tuple(files),
        issues=tuple(issues),
        recorded_manifest_path=recorded_manifest_path,
        recorded_count=recorded_count,
    )


def _resolve_test_root(repo_root: Path, test_root: Path) -> Path:
    path = Path(test_root)
    if not path.is_absolute():
        path = repo_root / path
    path = path.resolve()
    if not path.is_relative_to(repo_root):
        raise ValueError(f"test root is outside repository: {path}")
    return path


def _selected_test_files(
    repo_root: Path,
    test_root: Path,
    paths: Sequence[str],
    all_files: bool,
) -> list[Path]:
    if paths and all_files:
        raise ValueError("use either explicit paths or --all, not both")
    if paths:
        return discover_test_files(repo_root, mode="requested", paths=paths)
    if all_files:
        return discover_test_files(repo_root, mode="all", test_root=test_root)
    return discover_test_files(repo_root, mode="changed", test_root=test_root)


def _extract_and_lint_tests(
    files: Sequence[Path],
    repo_root: Path,
) -> tuple[dict[Path, list[ExtractedTestRecord]], list[LintIssue]]:
    tests_by_file: dict[Path, list[ExtractedTestRecord]] = {}
    issues: list[LintIssue] = []
    for test_file in sorted({Path(path).resolve() for path in files}):
        try:
            tests = extract_tests_from_file(test_file, repo_root)
        except (OSError, SyntaxError) as error:
            issues.append(
                LintIssue(
                    path=_relative_path(test_file, repo_root),
                    test_name="<module>",
                    line=1,
                    rule="parse_error",
                    message=f"could not parse test file: {error}",
                )
            )
            continue
        tests_by_file[test_file] = tests
        for test in tests:
            issues.extend(run_conventional_linter(test))
    return tests_by_file, issues


def _write_missing_or_stale_agent_review_artifacts(
    files: Sequence[Path],
    repo_root: Path,
    artifact_root: Path,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]],
) -> None:
    for test_file in files:
        for test in tests_by_file[test_file.resolve()]:
            artifact_path = map_test_function_to_agent_md_file(
                test_file,
                repo_root,
                artifact_root,
                test.name,
            )
            if not artifact_path.exists() or _agent_md_file_is_stale(test_file, artifact_path):
                render_agent_md_file(test_file, test, repo_root, artifact_root)


def _lint_agent_review_artifacts(
    files: Sequence[Path],
    repo_root: Path,
    artifact_root: Path,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]],
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for test_file in files:
        for test in tests_by_file[test_file.resolve()]:
            issues.extend(
                _lint_agent_md_file(
                    test_file,
                    repo_root=repo_root,
                    artifact_root=artifact_root,
                    test_name=test.name,
                )
            )
    return issues


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path
