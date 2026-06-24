"""Command-line interface for agentic-tdd-linter."""

from __future__ import annotations

import argparse
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Sequence

from .agent_review_artifacts import agent_review_artifact_path
from .agent_ran_proof import agent_review_artifact_is_stale, lint_agent_review_artifact
from .agent_review_manifest import lint_agent_review_manifest, record_agent_review_attestations
from .agentic_md import write_agentic_md_for_test_file
from .docstrings import all_test_files, changed_test_files, lint_test_files, requested_test_files
from .report import format_json, format_text


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.refactor_instructions:
        print(_refactor_instructions_text())
        return 0

    if args.command == "check":
        return _run_check(args)

    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-tdd-linter",
        description="Lint Python tests written during agent-assisted TDD.",
    )
    parser.add_argument(
        "--refactor-instructions",
        action="store_true",
        help="print refactor-phase agent instructions and exit",
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="lint changed or requested test files")
    _add_file_selection_arguments(check_parser)
    check_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    check_parser.add_argument(
        "--repo-root",
        type=Path,
        help="repository root; defaults to the current git repository root",
    )
    check_parser.add_argument(
        "--test-root",
        type=Path,
        default=Path("tests"),
        help="test root used for --all selection and review artifacts; defaults to tests",
    )
    check_parser.add_argument(
        "--review-proof",
        choices=("auto", "artifact", "manifest"),
        default="auto",
        help=(
            "review proof source; auto accepts a current manifest before falling back to "
            "local .agent.md artifacts"
        ),
    )
    check_parser.add_argument(
        "--manifest",
        type=Path,
        help="manifest path; defaults to tests/agentic_review_manifest.jsonl",
    )
    check_parser.add_argument(
        "--reviewer",
        help=(
            "reviewer identity to store in the manifest after artifact proof passes, "
            "such as codex:gpt-5.5"
        ),
    )

    return parser


def _add_file_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("paths", nargs="*", help="test files or directories to lint")
    parser.add_argument(
        "--all",
        action="store_true",
        help="lint all project test files instead of changed test files",
    )


def _run_check(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve() if args.repo_root else _find_repo_root(Path.cwd())

    try:
        test_root = _resolve_test_root(repo_root, args.test_root)
        artifact_root = test_root / "agentic_review_artifacts"
        files = _selected_test_files(args, repo_root, test_root)
    except ValueError as error:
        print(f"agentic-tdd-linter: {error}", file=sys.stderr)
        return 2

    issues = lint_test_files(files, repo_root)
    recorded_manifest_path: Path | None = None
    recorded_count = 0
    if args.review_proof == "manifest":
        issues.extend(lint_agent_review_manifest(files, repo_root, args.manifest))
    elif args.review_proof == "artifact":
        _write_missing_or_stale_agent_review_artifacts(files, repo_root, artifact_root)
        issues.extend(_lint_agent_review_artifacts(files, repo_root, artifact_root))
        if not issues:
            manifest_path, count, manifest_issues = record_agent_review_attestations(
                files,
                repo_root,
                reviewer=args.reviewer or "",
                manifest_path=args.manifest,
                artifact_root=artifact_root,
            )
            issues.extend(manifest_issues)
            if not manifest_issues:
                recorded_manifest_path = manifest_path
                recorded_count = count
    else:
        manifest_issues = lint_agent_review_manifest(files, repo_root, args.manifest)
        if manifest_issues:
            _write_missing_or_stale_agent_review_artifacts(files, repo_root, artifact_root)
            issues.extend(_lint_agent_review_artifacts(files, repo_root, artifact_root))
            if not issues:
                manifest_path, count, refresh_issues = record_agent_review_attestations(
                    files,
                    repo_root,
                    reviewer=args.reviewer or "",
                    manifest_path=args.manifest,
                    artifact_root=artifact_root,
                )
                issues.extend(refresh_issues)
                if not refresh_issues:
                    recorded_manifest_path = manifest_path
                    recorded_count = count

    if args.format == "json":
        print(format_json(issues, files))
    else:
        print(format_text(issues, files))
        if not issues and recorded_manifest_path is not None:
            relative_manifest = _relative_path(recorded_manifest_path, repo_root)
            print(
                "agentic-tdd-linter: "
                f"recorded {recorded_count} review attestations in {relative_manifest}"
            )
    return 1 if issues else 0


def _selected_test_files(args: argparse.Namespace, repo_root: Path, test_root: Path) -> list[Path]:
    if args.paths and args.all:
        raise ValueError("use either explicit paths or --all, not both")
    if args.paths:
        return requested_test_files(args.paths, repo_root)
    if args.all:
        return all_test_files(repo_root, test_root)
    return [path for path in changed_test_files(repo_root) if path.is_relative_to(test_root)]


def _resolve_test_root(repo_root: Path, test_root: Path) -> Path:
    root = Path(repo_root).resolve()
    path = Path(test_root)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"test root is outside repository: {path}")
    return path


def _write_missing_or_stale_agent_review_artifacts(
    files: Sequence[Path],
    repo_root: Path,
    artifact_root: Path,
) -> None:
    for test_file in files:
        artifact_path = agent_review_artifact_path(test_file, repo_root, artifact_root)
        if not artifact_path.exists() or agent_review_artifact_is_stale(test_file, artifact_path):
            write_agentic_md_for_test_file(test_file, repo_root, artifact_root)


def _lint_agent_review_artifacts(files: Sequence[Path], repo_root: Path, artifact_root: Path):
    issues = []
    for test_file in files:
        issues.extend(
            lint_agent_review_artifact(
                test_file,
                repo_root=repo_root,
                artifact_root=artifact_root,
            )
        )
    return issues


def _refactor_instructions_text() -> str:
    return resources.files("agentic_tdd_linter").joinpath("refactor_instructions.md").read_text(
        encoding="utf-8"
    )


def _find_repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip()).resolve()
    return start.resolve()


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
