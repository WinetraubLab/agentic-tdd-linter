"""Run test-relationship YAML examples through docstring-only review."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple

from agentic_tdd_linter.agentic_linter.render_cross_test_agent_md_file import (
    _relationship_review_input_scope,
    _render_test_relationship_docstrings_agent_md,
)

from .agent_review_examples import (
    SCORECARD_ROW_PATTERN,
    _scorecard_mismatch_message,
    _scorecard_mismatches,
)
from .test_relationship_review_yaml_fixture_contract import (
    EXAMPLES,
    criterion_titles_from_template,
    lint_test_relationship_review_examples,
    read_test_relationship_review_examples,
    relationship_review_example_files,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
ANONYMOUS_ROOT = (
    REPO_ROOT / "temporary_fixtures" / "test_relationship_review_examples"
)
ARTIFACT_ROOT = ANONYMOUS_ROOT / "agentic_review_artifacts"
REPORT_PATH = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "test_relationship_review_example_runner.json"
)
_SCORECARD_PATTERN = re.compile(
    r"^## Review Scorecard\s*\n+"
    r"Test:\s*`([^`]+)`\s*\n"
    r"(.*?)(?=^## Review Scorecard|\Z)",
    re.MULTILINE | re.DOTALL,
)
_PAIR_CLASSIFICATION_PATTERN = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*"
    r"(pending|yes|no)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE | re.IGNORECASE,
)


class TestRelationshipReviewRunResult(NamedTuple):
    agent_md_files: tuple[Path, ...]


def run_test_relationship_review_examples(
    *,
    examples_path: Path = EXAMPLES,
    artifact_root: Path = ARTIFACT_ROOT,
    report_path: Path = REPORT_PATH,
) -> TestRelationshipReviewRunResult:
    """Run every test-relationship YAML example in one fixture folder."""

    schema_errors = lint_test_relationship_review_examples(
        examples_path=examples_path
    )
    if schema_errors:
        raise ValueError("\n".join(schema_errors))
    titles = criterion_titles_from_template()
    examples = [
        example
        for path in relationship_review_example_files(Path(examples_path))
        for example in read_test_relationship_review_examples(path, titles)
    ]
    duplicate_names = {
        example.name for example in examples if sum(
            item.name == example.name for item in examples
        ) > 1
    }
    if duplicate_names:
        raise ValueError(
            "test-relationship YAML case names must be unique: "
            + ", ".join(sorted(duplicate_names))
        )

    pending_packets: list[Path] = []
    mismatches = []
    tested_cases_by_criterion: dict[int, int] = {}
    for example in examples:
        packet_text = _render_test_relationship_docstrings_agent_md(
            [
                (test.identifier, test.docstring)
                for test in example.tests
            ]
        )
        artifact_path = Path(artifact_root) / f"{_safe_name(example.name)}.agent.md"
        if (
            not artifact_path.exists()
            or _relationship_review_input_scope(
                artifact_path.read_text(encoding="utf-8")
            )
            != _relationship_review_input_scope(packet_text)
        ):
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(packet_text, encoding="utf-8")
        artifact_text = artifact_path.read_text(encoding="utf-8")
        pair_classifications = _requirement_overlap_results(artifact_text)
        scorecards = _test_relationship_scorecard_results(artifact_text)
        if _pair_classifications_are_pending(
            pair_classifications
        ) or _scorecards_are_pending(scorecards):
            pending_packets.append(artifact_path)
            continue
        expected_pair = (
            example.tests[0].identifier,
            example.tests[1].identifier,
        )
        if set(pair_classifications) != {expected_pair}:
            raise ValueError(
                f"{example.name} pair classifications do not match "
                "the two test identifiers"
            )
        tested_cases_by_criterion[10] = (
            tested_cases_by_criterion.get(10, 0) + 1
        )
        mismatches.extend(
            _scorecard_mismatches(
                example_name=f"{example.name}/pair",
                test_name=f"{expected_pair[0]} <> {expected_pair[1]}",
                expected_scorecard={
                    10: example.expected_requirement_overlap,
                },
                actual_scorecard={
                    10: pair_classifications[expected_pair],
                },
            )
        )
        expected_identifiers = {test.identifier for test in example.tests}
        if set(scorecards) != expected_identifiers:
            missing = sorted(expected_identifiers - set(scorecards))
            extra = sorted(set(scorecards) - expected_identifiers)
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if extra:
                details.append("unexpected: " + ", ".join(extra))
            raise ValueError(
                f"{example.name} scorecards do not match test identifiers "
                f"({'; '.join(details)})"
            )
        for test in example.tests:
            expected_scorecard = {
                number: expectation.result
                for number, expectation in test.expected_scorecard.items()
            }
            for criterion in expected_scorecard:
                tested_cases_by_criterion[criterion] = (
                    tested_cases_by_criterion.get(criterion, 0) + 1
                )
            mismatches.extend(
                _scorecard_mismatches(
                    example_name=f"{example.name}/{test.key}",
                    test_name=test.identifier,
                    expected_scorecard=expected_scorecard,
                    actual_scorecard=scorecards[test.identifier],
                )
            )

    if pending_packets:
        packet_list = "\n".join(
            f"- {_display_path(path)}" for path in sorted(set(pending_packets))
        )
        raise RuntimeError(
            "test-relationship examples are pending; review only these "
            f"Markdown packets, then rerun:\n{packet_list}"
        )

    reviewer_model = _reviewer_model_from_environment()
    _write_report(
        report_path=Path(report_path),
        examples=examples,
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        reviewer_model=reviewer_model,
    )
    if mismatches:
        raise AssertionError(
            _scorecard_mismatch_message(
                mismatches,
                tested_cases_by_criterion=tested_cases_by_criterion,
            )
        )
    return TestRelationshipReviewRunResult(
        agent_md_files=tuple(sorted(Path(artifact_root).glob("*.agent.md")))
    )


def _test_relationship_scorecard_results(
    text: str,
) -> dict[str, dict[int, str]]:
    scorecards: dict[str, dict[int, str]] = {}
    for scorecard_match in _SCORECARD_PATTERN.finditer(text):
        identifier = scorecard_match.group(1).strip()
        if identifier in scorecards:
            raise ValueError(
                f"duplicate test-relationship scorecard for {identifier}"
            )
        results: dict[int, str] = {}
        for row_match in SCORECARD_ROW_PATTERN.finditer(scorecard_match.group(2)):
            criterion = int(row_match.group(1))
            if criterion in results:
                raise ValueError(
                    f"{identifier} duplicates scorecard criterion {criterion}"
                )
            results[criterion] = row_match.group(3).strip().lower()
        if not results:
            raise ValueError(f"{identifier} scorecard contains no criterion rows")
        scorecards[identifier] = results
    if not scorecards:
        raise ValueError(
            "test-relationship review packet contains no scorecards"
        )
    return scorecards


def _requirement_overlap_results(
    text: str,
) -> dict[tuple[str, str], str]:
    classifications: dict[tuple[str, str], str] = {}
    for match in _PAIR_CLASSIFICATION_PATTERN.finditer(text):
        pair = (match.group(1).strip(), match.group(2).strip())
        if pair in classifications:
            raise ValueError(
                "duplicate requirement-description overlap classification "
                f"for {pair[0]} and {pair[1]}"
            )
        classifications[pair] = match.group(3).strip().lower()
    if not classifications:
        raise ValueError(
            "test-relationship review packet contains no pair classifications"
        )
    return classifications


def _pair_classifications_are_pending(
    classifications: dict[tuple[str, str], str],
) -> bool:
    return any(
        result not in {"yes", "no"}
        for result in classifications.values()
    )


def _scorecards_are_pending(
    scorecards: dict[str, dict[int, str]],
) -> bool:
    return any(
        result not in {"pass", "fail"}
        for scorecard in scorecards.values()
        for result in scorecard.values()
    )

def _safe_name(name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    if not safe_name:
        raise ValueError(
            "test-relationship YAML case name needs a filesystem-safe character"
        )
    return safe_name


def _reviewer_model_from_environment() -> str:
    import os

    reviewer_model = os.environ.get("AGENT_REVIEW_MODEL", "").strip()
    if not reviewer_model:
        raise RuntimeError(
            "set AGENT_REVIEW_MODEL to the model and reasoning level used "
            "for test-relationship review"
        )
    return reviewer_model


def _write_report(
    *,
    report_path: Path,
    examples: list[object],
    mismatches: list[object],
    tested_cases_by_criterion: dict[int, int],
    reviewer_model: str,
) -> None:
    failing_cases_by_criterion: dict[int, set[str]] = {}
    for mismatch in mismatches:
        failing_cases_by_criterion.setdefault(mismatch.criterion, set()).add(
            mismatch.yaml_case
        )
    criteria: dict[str, dict[str, object]] = {}
    for criterion, total in sorted(tested_cases_by_criterion.items()):
        failing_cases = sorted(failing_cases_by_criterion.get(criterion, set()))
        passing = total - len(failing_cases)
        criteria[str(criterion)] = {
            "success": f"{passing}/{total} ({_percentage(passing, total)} pass)",
            "enforced_checks": total,
            "failing_yaml_cases": failing_cases,
        }
    total_checks = sum(tested_cases_by_criterion.values())
    total_failures = sum(
        len(failing_cases) for failing_cases in failing_cases_by_criterion.values()
    )
    total_passing = total_checks - total_failures
    report = {
        "review_type": "test-relationship",
        "review_type_aliases": ["cross-test", "relational", "Similar Coverage"],
        "reviewer": {"model": reviewer_model},
        "total": {
            "success": (
                f"{total_passing}/{total_checks} "
                f"({_percentage(total_passing, total_checks)} pass)"
            ),
            "enforced_checks": total_checks,
        },
        "yaml_cases": len(examples),
        "test_docstrings": sum(len(example.tests) for example in examples),
        "criteria": criteria,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _percentage(numerator: int, denominator: int) -> str:
    percentage = f"{100 * numerator / denominator:.1f}".rstrip("0").rstrip(".")
    return f"{percentage}%"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> None:
    run_test_relationship_review_examples()


if __name__ == "__main__":
    main()
