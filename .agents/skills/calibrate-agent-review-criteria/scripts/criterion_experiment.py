#!/usr/bin/env python3
"""Prepare and compare one blind agent-review criterion experiment."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import textwrap
from pathlib import Path


def main() -> int:
    args = _arguments()
    root = _repository_root(Path.cwd())
    sys.path[:0] = [str(root), str(root / "src")]
    if args.command == "prepare":
        return _prepare(root, args)
    return _compare(root, args)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare or compare one isolated criterion experiment."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    _add_case_arguments(prepare)
    prepare.add_argument("--current", action="store_true")
    prepare.add_argument("--title")
    prepare.add_argument("--rule", action="append")

    compare = subparsers.add_parser("compare")
    _add_case_arguments(compare)
    compare.add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        if args.current and (args.title or args.rule):
            parser.error("--current cannot be combined with --title or --rule")
        if not args.current and (not args.title or not args.rule):
            parser.error("prepare requires --current or both --title and --rule")
    return args


def _add_case_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("case")
    parser.add_argument("criterion", type=int)


def _repository_root(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / "pyproject.toml").exists() and (
            candidate / "tests" / "agentic_linter" / "fixtures" / "single_test_review"
        ).is_dir():
            return candidate
    raise SystemExit("run inside the agentic-tdd-lint repository")


def _examples(root: Path):
    from tests.agentic_linter.test_harness.agent_review_yaml_fixture_contract import (
        agent_review_example_files,
        criterion_titles_from_template,
        read_agent_review_examples,
    )

    fixture_root = root / "tests" / "agentic_linter" / "fixtures" / "single_test_review"
    titles = criterion_titles_from_template()
    return [
        example
        for path in agent_review_example_files(fixture_root)
        for example in read_agent_review_examples(path, titles)
    ]


def _example(root: Path, name: str):
    matches = [example for example in _examples(root) if example.name == name]
    if len(matches) != 1:
        raise SystemExit(f"expected one YAML example named {name!r}, found {len(matches)}")
    return matches[0]


def _prepare(root: Path, args: argparse.Namespace) -> int:
    from agentic_tdd_linter.agentic_linter.render_agent_md_file import (
        render_agent_md_file,
    )
    from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
        extract_tests_from_file,
    )

    example = _example(root, args.case)
    source = (
        textwrap.dedent(example.file_docstring).strip()
        + "\n\n"
        + textwrap.dedent(example.test).strip()
        + "\n"
    )
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    anonymous_root = root / "temporary_fixtures" / "agent_review_examples"
    source_path = anonymous_root / f"test_{digest}.py"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8")
    tests = extract_tests_from_file(source_path, root)
    if len(tests) != 1:
        raise SystemExit(
            f"criterion experiments require exactly one extracted test, found {len(tests)}"
        )
    packet = render_agent_md_file(
        source_path,
        tests[0],
        root,
        anonymous_root / "agentic_review_artifacts",
    )
    if not args.current:
        text = packet.read_text(encoding="utf-8")
        text = _replace_criterion(text, args.criterion, args.title, args.rule)
        text = _replace_scorecard_title(text, args.criterion, args.title)
        packet.write_text(text, encoding="utf-8")
    print(packet.relative_to(root))
    return 0


def _replace_criterion(
    packet: str, criterion: int, title: str, rules: list[str]
) -> str:
    pattern = re.compile(
        rf"^#### {criterion}\. .+?\n.*?(?=^#### \d+\.|^### |^## )",
        re.MULTILINE | re.DOTALL,
    )
    replacement = f"#### {criterion}. {title}\n" + "\n".join(rules) + "\n\n"
    updated, count = pattern.subn(replacement, packet, count=1)
    if count != 1:
        raise SystemExit(f"packet does not contain exactly one criterion {criterion}")
    return updated


def _replace_scorecard_title(packet: str, criterion: int, title: str) -> str:
    pattern = re.compile(rf"^(\|\s*{criterion}\s*\|)\s*[^|]+?\s*(\|)", re.MULTILINE)
    updated, count = pattern.subn(rf"\1 {title} \2", packet, count=1)
    if count != 1:
        raise SystemExit(f"packet does not contain scorecard row {criterion}")
    return updated


def _compare(root: Path, args: argparse.Namespace) -> int:
    example = _example(root, args.case)
    expectation = example.expected_scorecard.get(args.criterion)
    if expectation is None:
        raise SystemExit(
            f"example {args.case!r} has no expectation for criterion {args.criterion}"
        )
    packet = args.packet if args.packet.is_absolute() else root / args.packet
    actual = _scorecard_result(packet.read_text(encoding="utf-8"), args.criterion)
    expected = expectation.result
    print(f"expected={expected}")
    print(f"actual={actual}")
    print(f"mismatch={str(actual != expected).lower()}")
    return int(actual != expected)


def _scorecard_result(packet: str, criterion: int) -> str:
    match = re.search(
        rf"^\|\s*{criterion}\s*\|\s*[^|]+\|\s*([^|]+?)\s*\|",
        packet,
        re.MULTILINE,
    )
    if match is None:
        raise SystemExit(f"packet has no scorecard row {criterion}")
    return match.group(1).strip().lower()


if __name__ == "__main__":
    raise SystemExit(main())
