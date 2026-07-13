"""Parse command-line arguments and present lint-pipeline results."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .format_linter_results import format_json, format_text
from .run_lint_pipeline import run_lint_pipeline


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "check":
        parser.print_help()
        return 2

    repo_root = args.repo_root.resolve() if args.repo_root else _find_repo_root(Path.cwd())
    try:
        result = run_lint_pipeline(
            repo_root=repo_root,
            test_root=args.test_root,
            paths=args.paths,
            all_files=args.all,
            review_proof=args.review_proof,
            manifest_path=args.manifest,
            reviewer=args.reviewer or "",
        )
    except ValueError as error:
        print(f"agentic-tdd-linter: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(format_json(result.issues, result.files))
    else:
        print(format_text(result.issues, result.files))
        if not result.issues and result.recorded_manifest_path is not None:
            relative_manifest = _relative_path(result.recorded_manifest_path, repo_root)
            print(
                "agentic-tdd-linter: "
                f"recorded {result.recorded_count} review attestations in {relative_manifest}"
            )
    return 1 if result.issues else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-tdd-linter",
        description="Lint Python and TypeScript tests written during agent-assisted TDD.",
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
