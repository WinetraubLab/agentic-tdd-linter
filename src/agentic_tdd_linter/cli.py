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
    check_parser.add_argument("paths", nargs="*", help="test files or directories to lint")
    check_parser.add_argument(
        "--all",
        action="store_true",
        help="lint all project test files instead of changed test files",
    )
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

    return parser


def _run_check(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve() if args.repo_root else _find_repo_root(Path.cwd())

    try:
        if args.paths and args.all:
            raise ValueError("use either explicit paths or --all, not both")
        if args.paths:
            files = requested_test_files(args.paths, repo_root)
        elif args.all:
            files = all_test_files(repo_root)
        else:
            files = changed_test_files(repo_root)
    except ValueError as error:
        print(f"agentic-tdd-linter: {error}", file=sys.stderr)
        return 2

    _write_missing_or_stale_agent_review_artifacts(files, repo_root)

    issues = lint_test_files(files, repo_root)
    issues.extend(_lint_agent_review_artifacts(files, repo_root))

    if args.format == "json":
        print(format_json(issues, files))
    else:
        print(format_text(issues, files))
    return 1 if issues else 0


def _write_missing_or_stale_agent_review_artifacts(files: Sequence[Path], repo_root: Path) -> None:
    for test_file in files:
        artifact_path = agent_review_artifact_path(test_file, repo_root)
        if not artifact_path.exists() or agent_review_artifact_is_stale(test_file, artifact_path):
            write_agentic_md_for_test_file(test_file, repo_root)


def _lint_agent_review_artifacts(files: Sequence[Path], repo_root: Path):
    issues = []
    for test_file in files:
        issues.extend(lint_agent_review_artifact(test_file, repo_root=repo_root))
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


if __name__ == "__main__":
    raise SystemExit(main())
