"""Coordinate test discovery, linting, and agent-review proof checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from ..agentic_linter.build_manifest_from_agent_md_files import (
    build_manifest_from_agent_md_files,
    _find_files_with_changed_test_content,
    _find_tests_requiring_agent_review,
)
from ..agentic_linter.determine_agent_md_status import (
    _agent_md_file_is_stale,
    _lint_agent_md_file,
)
from ..agentic_linter.map_test_function_to_agent_md_file import (
    map_test_function_to_agent_md_file,
)
from ..agentic_linter.render_agent_md_file import render_agent_md_file
from ..agentic_linter.render_cross_test_agent_md_file import (
    cross_test_agent_md_file_is_stale,
    render_cross_test_agent_md_file,
)
from ..conventional_linter.check_file_docstring_term_count import (
    check_file_docstring_term_count,
)
from ..conventional_linter.check_test_module_contract import (
    check_test_module_contract,
)
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
    generated_artifacts: tuple[Path, ...] = ()


def run_lint_pipeline(
    *,
    repo_root: Path,
    test_root: Path = Path("tests"),
    paths: Sequence[str] = (),
    force_fresh: bool = False,
    manifest_path: Path | None = None,
    reviewer: str = "",
) -> LintPipelineResult:
    """Lint tests that do not have current passing manifest proof."""

    root = Path(repo_root).resolve()
    resolved_test_root = _resolve_test_root(root, test_root)
    artifact_root = resolved_test_root / "agentic_review_artifacts"
    files = _selected_test_files(root, resolved_test_root, paths)
    tests_by_file, issues = _extract_tests(files, root)
    if issues:
        return LintPipelineResult(files=tuple(files), issues=tuple(issues))
    review_files = [test_file for test_file in files if tests_by_file.get(test_file.resolve())]
    issues.extend(_run_conventional_checks(tests_by_file, root))
    if issues:
        return LintPipelineResult(files=tuple(files), issues=tuple(issues))
    pending_by_file = _find_tests_requiring_agent_review(
        review_files,
        root,
        manifest_path,
        tests_by_file=tests_by_file,
        force_all=force_fresh,
    )
    pending_files = [path for path, tests in pending_by_file.items() if tests]
    missing_artifact_issues = _missing_required_artifact_issues(
        pending_files,
        root,
        artifact_root,
        pending_by_file,
        force_fresh=force_fresh,
    )
    if missing_artifact_issues:
        return LintPipelineResult(files=tuple(files), issues=tuple(missing_artifact_issues))

    issues.extend(
        _lint_agent_review_artifacts(
            pending_files,
            root,
            artifact_root,
            pending_by_file,
        )
    )

    recorded_manifest_path: Path | None = None
    recorded_count = 0
    if pending_files and not issues:
        recorded_manifest_path, recorded_count, issues = build_manifest_from_agent_md_files(
            pending_files,
            root,
            reviewer=reviewer,
            manifest_path=manifest_path,
            artifact_root=artifact_root,
            tests_by_file=pending_by_file,
            preserve_unselected_tests=not force_fresh,
        )
        if issues:
            recorded_manifest_path = None
            recorded_count = 0

    return LintPipelineResult(
        files=tuple(files),
        issues=tuple(issues),
        recorded_manifest_path=recorded_manifest_path,
        recorded_count=recorded_count,
    )


def create_agent_md_files(
    *,
    repo_root: Path,
    test_root: Path = Path("tests"),
    paths: Sequence[str] = (),
    force_fresh: bool = False,
    manifest_path: Path | None = None,
) -> LintPipelineResult:
    """Create review packets for tests without current manifest proof."""

    root = Path(repo_root).resolve()
    resolved_test_root = _resolve_test_root(root, test_root)
    artifact_root = resolved_test_root / "agentic_review_artifacts"
    files = _selected_test_files(root, resolved_test_root, paths)
    tests_by_file, issues = _extract_tests(files, root)
    if issues:
        return LintPipelineResult(files=tuple(files), issues=tuple(issues))
    review_files = [test_file for test_file in files if tests_by_file.get(test_file.resolve())]
    issues.extend(_run_conventional_checks(tests_by_file, root))
    if issues:
        return LintPipelineResult(files=tuple(files), issues=tuple(issues))
    cross_review_files = (
        review_files
        if force_fresh
        else _find_files_with_changed_test_content(
            review_files,
            root,
            manifest_path,
            tests_by_file=tests_by_file,
        )
    )
    pending_by_file = _find_tests_requiring_agent_review(
        review_files,
        root,
        manifest_path,
        tests_by_file=tests_by_file,
        force_all=force_fresh,
    )
    if force_fresh and not paths:
        _clear_agent_md_files(artifact_root)

    generated: list[Path] = []
    for test_file, tests in pending_by_file.items():
        for test in tests:
            artifact_path = map_test_function_to_agent_md_file(
                test_file,
                root,
                artifact_root,
                test.name,
            )
            if (
                force_fresh
                or not artifact_path.exists()
                or _agent_md_file_is_stale(test.source, artifact_path)
            ):
                generated.append(render_agent_md_file(test_file, test, root, artifact_root))
    if cross_review_files and (
        force_fresh
        or cross_test_agent_md_file_is_stale(
            cross_review_files,
            root,
            artifact_root,
        )
    ):
        generated.append(
            render_cross_test_agent_md_file(cross_review_files, root, artifact_root)
        )
    return LintPipelineResult(
        files=tuple(files),
        issues=(),
        generated_artifacts=tuple(generated),
    )


def _clear_agent_md_files(artifact_root: Path) -> None:
    if not artifact_root.exists():
        return
    for artifact_path in artifact_root.glob("*.agent.md"):
        artifact_path.unlink()


def _run_conventional_checks(
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]],
    repo_root: Path,
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for file_tests in tests_by_file.values():
        if file_tests:
            issues.extend(check_test_module_contract(file_tests, repo_root))
            issues.extend(check_file_docstring_term_count(file_tests[0]))
        for test in file_tests:
            issues.extend(run_conventional_linter(test))
    return issues


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
) -> list[Path]:
    if paths:
        return discover_test_files(repo_root, mode="requested", paths=paths)
    return discover_test_files(repo_root, mode="all", test_root=test_root)


def _extract_tests(
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
    return tests_by_file, issues


def _missing_required_artifact_issues(
    files: Sequence[Path],
    repo_root: Path,
    artifact_root: Path,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]],
    *,
    force_fresh: bool,
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for test_file in files:
        for test in tests_by_file[test_file.resolve()]:
            artifact_path = map_test_function_to_agent_md_file(
                test_file,
                repo_root,
                artifact_root,
                test.name,
            )
            if not artifact_path.exists() or _agent_md_file_is_stale(
                test.source,
                artifact_path,
            ):
                command = "agentic-tdd-linter create-agent-md"
                if force_fresh:
                    command += " --fresh"
                command += f" {_relative_path(test_file, repo_root)}"
                issues.append(
                    LintIssue(
                        path=_relative_path(artifact_path, repo_root),
                        test_name=test.name,
                        line=1,
                        rule="missing_required_agent_md",
                        message=(
                            "required agent review packet is missing or stale; "
                            f"run `{command}` before `agentic-tdd-linter lint`"
                        ),
                    )
                )
    return issues


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
                    test_source=test.source,
                )
            )
    return issues


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path
