"""Parse command-line arguments and present lint-pipeline results."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from ..conventional_linter.run_conventional_linter import LintIssue
from .format_linter_results import format_json, format_text
from .run_lint_pipeline import create_agent_md_files, run_lint_pipeline


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command not in {"lint", "create-agent-md"}:
        parser.print_help()
        return 2

    if args.all:
        print(
            "agentic-tdd-linter: --all is deprecated; use --fresh",
            file=sys.stderr,
        )

    repo_root = args.repo_root.resolve() if args.repo_root else _find_repo_root(Path.cwd())
    try:
        common_arguments = {
            "repo_root": repo_root,
            "test_root": args.test_root,
            "paths": args.paths,
            "force_fresh": args.fresh or args.all,
            "manifest_path": args.manifest,
        }
        if args.command == "create-agent-md":
            result = create_agent_md_files(**common_arguments)
        else:
            result = run_lint_pipeline(
                **common_arguments,
                reviewer=args.reviewer or "",
            )
    except ValueError as error:
        print(f"agentic-tdd-linter: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(format_json(result.issues, result.files))
    elif args.command == "create-agent-md" and not result.issues:
        print(
            "agentic-tdd-linter: "
            f"generated {len(result.generated_artifacts)} agent review packets"
        )
    else:
        print(format_text(result.issues, result.files))
        if not result.issues and result.recorded_manifest_path is not None:
            relative_manifest = _relative_path(result.recorded_manifest_path, repo_root)
            print(
                "agentic-tdd-linter: "
                f"recorded {result.recorded_count} review attestations in {relative_manifest}"
            )
    if args.format == "text":
        next_action = _next_action(
            args.command,
            result.issues,
            generated_count=len(result.generated_artifacts),
        )
        if next_action:
            print(next_action)
    return 1 if result.issues else 0


def _next_action(
    command: str,
    issues: Sequence[LintIssue],
    *,
    generated_count: int,
) -> str:
    """Return coordinator guidance for the current review-workflow state."""

    rules = {issue.rule for issue in issues}
    if "agent_review_failed" in rules:
        return "\n".join(
            (
                "Next action:",
                "1. Collect every failure from every selected packet before editing.",
                "2. Make one consolidated source edit that addresses all collected failures.",
                "3. Run the affected unit tests and finish all source edits before review.",
                "4. Regenerate the selected packets once with "
                "`agentic-tdd-linter create-agent-md --fresh`.",
                "5. Do not retry an unchanged criterion to obtain a different result; "
                "report a workflow conflict.",
            )
        )
    if "agent_review_not_run" in rules:
        return "\n".join(
            (
                "Next action:",
                "1. Keep the reviewed source stable.",
                "2. Complete every scorecard with one fresh isolated reviewer per criterion.",
                "3. Rerun `agentic-tdd-linter lint` after every selected packet is complete.",
            )
        )
    if rules.intersection(
        {
            "missing_required_agent_md",
            "missing_agent_review_artifact",
            "stale_agent_review_artifact",
        }
    ):
        return "\n".join(
            (
                "Next action:",
                "1. Finish all source edits and run the affected unit tests.",
                "2. Generate the selected packets once with `agentic-tdd-linter create-agent-md`.",
                "3. Keep the source stable while every generated scorecard is reviewed.",
            )
        )
    if command == "create-agent-md" and not issues and generated_count:
        return "\n".join(
            (
                "Next action:",
                "1. Run the affected unit tests and finish all source edits before review.",
                "2. If source changed after packet generation, regenerate once with "
                "`agentic-tdd-linter create-agent-md --fresh`.",
                "3. Keep the source stable while every generated scorecard is reviewed "
                "with one fresh isolated reviewer per criterion.",
                "4. If review fails, collect every packet failure before editing; make one "
                "consolidated edit, rerun tests, and regenerate once.",
                "5. Do not retry an unchanged criterion to obtain a different result; "
                "report a workflow conflict.",
            )
        )
    return ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-tdd-linter",
        description="Lint Python and TypeScript tests written during agent-assisted TDD.",
    )
    subparsers = parser.add_subparsers(dest="command")

    lint_parser = subparsers.add_parser(
        "lint",
        help="lint tests without current manifest proof",
    )
    create_parser = subparsers.add_parser(
        "create-agent-md",
        help="create required agent review packets",
    )
    for command_parser in (lint_parser, create_parser):
        _add_file_selection_arguments(command_parser)
        _add_shared_arguments(command_parser)

    lint_parser.add_argument(
        "--reviewer",
        help=(
            "reviewer identity to store in the manifest after artifact proof passes, "
            "such as codex:gpt-5.5"
        ),
    )

    return parser


def _add_file_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("paths", nargs="*", help="test files or directories to process")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help=(
            "ignore previous review proof and regenerate every packet in the selected "
            "scope, including the cross-test packet; without paths, use the whole test root"
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="deprecated alias for --fresh",
    )


def _add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="repository root; defaults to the current git repository root",
    )
    parser.add_argument(
        "--test-root",
        type=Path,
        default=Path("tests"),
        help="test root used for discovery and review artifacts; defaults to tests",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="manifest path; defaults to tests/agentic_review_manifest.jsonl",
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
