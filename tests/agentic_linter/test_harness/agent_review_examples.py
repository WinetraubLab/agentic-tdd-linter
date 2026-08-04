"""Provide reusable mechanics for anonymous agent-review integration tests."""

from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, NamedTuple

from agentic_tdd_linter.version import __version__

REPO_ROOT = Path(__file__).resolve().parents[3]
SCORECARD_ROW_PATTERN = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class _ScorecardMismatch:
    yaml_case: str
    test_name: str
    criterion: int
    expected: str
    actual: str


@dataclass(frozen=True)
class _AgentReviewCase:
    yaml_case: str
    test_name: str
    mismatch_name: str
    source_sha256: str
    expected_scorecard: dict[int, str]
    completed_results: tuple[str, ...]
    artifact_path: Path


class _AgentReviewRunResult(NamedTuple):
    agent_md_files: tuple[Path, ...]


def _validate_yaml_examples(
    examples_path: Path,
    lint_examples: Callable[..., list[str]],
) -> float:
    invocation_started_at = time.time()
    schema_errors = lint_examples(examples_path=examples_path)
    if schema_errors:
        raise ValueError("\n".join(schema_errors))
    return invocation_started_at


def _run_yaml_reviews(
    *,
    cases: list[_AgentReviewCase],
    yaml_case_count: int,
    artifact_root: Path,
    attestation_path: Path,
    report_path: Path,
    review_start_path: Path,
    evaluate: Callable[[_AgentReviewCase], dict[int, str] | None],
    pending_message: str,
    completion_instruction: str,
) -> _AgentReviewRunResult:
    attestations = _read_scorecard_attestations(attestation_path)
    pending_packets: list[Path] = []
    mismatches: list[_ScorecardMismatch] = []
    completed_attestations: list[dict[str, object]] = []
    tested_cases_by_criterion: dict[int, int] = {}
    reviewer_model = ""

    for case in cases:
        for criterion in case.expected_scorecard:
            tested_cases_by_criterion[criterion] = (
                tested_cases_by_criterion.get(criterion, 0) + 1
            )
        current_record = attestations.get((case.yaml_case, case.test_name))
        if _scorecard_attestation_is_current(
            current_record,
            source_sha256=case.source_sha256,
            expected_scorecard=case.expected_scorecard,
            completed_results=case.completed_results,
        ):
            actual_scorecard = {
                int(number): str(result)
                for number, result in current_record["actual_scorecard"].items()
            }
            reviewer = current_record["reviewer"]
        else:
            actual_scorecard = evaluate(case)
            if actual_scorecard is None:
                pending_packets.append(case.artifact_path)
                continue
            if not reviewer_model:
                reviewer_model = _reviewer_model_from_environment()
            reviewer = {"model": reviewer_model}

        completed_attestations.append(
            {
                "yaml_case": case.yaml_case,
                "test": case.test_name,
                "scorecard_scope": "expected_criteria",
                "source_sha256": case.source_sha256,
                "linter_version": __version__,
                "reviewer": reviewer,
                "expected_scorecard": {
                    str(number): result
                    for number, result in sorted(case.expected_scorecard.items())
                },
                "actual_scorecard": {
                    str(number): result
                    for number, result in sorted(actual_scorecard.items())
                },
            }
        )
        mismatches.extend(
            _scorecard_mismatches(
                example_name=case.mismatch_name,
                test_name=case.test_name,
                expected_scorecard=case.expected_scorecard,
                actual_scorecard=actual_scorecard,
            )
        )

    if pending_packets:
        packet_list = "\n".join(
            f"- {_display_path(path)}"
            for path in sorted(set(pending_packets))
        )
        raise RuntimeError(
            f"{pending_message}\n{packet_list}\n{completion_instruction}"
        )

    regressions, review_duration_seconds = _finish_yaml_evaluation(
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        baseline_path=report_path,
        start_path=review_start_path,
    )
    _write_scorecard_attestations(attestation_path, completed_attestations)
    _write_scorecard_sidecar(
        sidecar_path=report_path,
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        yaml_case_count=yaml_case_count,
        review_duration_seconds=review_duration_seconds,
        reviewer_model=_reviewer_model(completed_attestations),
    )
    if review_duration_seconds is not None:
        review_start_path.unlink()
    if regressions:
        raise AssertionError(
            _scorecard_mismatch_message(
                mismatches,
                tested_cases_by_criterion=tested_cases_by_criterion,
            )
            + "\n\nNew failures exceed the committed scorecard baseline:\n"
            + "\n".join(regressions)
        )
    return _AgentReviewRunResult(
        agent_md_files=tuple(sorted(artifact_root.glob("*.agent.md")))
    )


def _finish_yaml_evaluation(
    *,
    mismatches: list[_ScorecardMismatch],
    tested_cases_by_criterion: dict[int, int],
    baseline_path: Path,
    start_path: Path,
) -> tuple[list[str], float | None]:
    regressions = (
        _scorecard_regressions(
            mismatches,
            tested_cases_by_criterion=tested_cases_by_criterion,
            baseline_path=baseline_path,
        )
        if baseline_path.exists()
        else []
    )
    review_duration_seconds = _review_duration_seconds(
        start_path,
        completed_at=time.time(),
    )
    return regressions, review_duration_seconds


def _reviewer_model(records: list[dict[str, object]]) -> str:
    reviewer_models = {
        str(reviewer["model"])
        for record in records
        if isinstance((reviewer := record.get("reviewer")), dict)
        and reviewer.get("model")
    }
    if not reviewer_models:
        raise ValueError("completed attestations require reviewer model")
    if len(reviewer_models) == 1:
        return next(iter(reviewer_models))
    return f"multiple: {', '.join(sorted(reviewer_models))}"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _scorecard_regressions(
    mismatches: list[_ScorecardMismatch],
    *,
    tested_cases_by_criterion: dict[int, int],
    baseline_path: Path,
) -> list[str]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    for criterion, row in baseline["criteria"].items():
        total = row["enforced_checks"]
        passing = total - len(row["failing_yaml_cases"])
        expected_success = f"{passing}/{total} ({_percentage(passing, total)} pass)"
        if row["success"] != expected_success:
            raise ValueError(
                f"criterion {criterion} baseline success must be "
                f"{expected_success!r}; got {row['success']!r}"
            )
    total_checks = sum(
        row["enforced_checks"] for row in baseline["criteria"].values()
    )
    total_mismatches = sum(
        len(row["failing_yaml_cases"])
        for row in baseline["criteria"].values()
    )
    total_passing = total_checks - total_mismatches
    expected_total = {
        "success": (
            f"{total_passing}/{total_checks} "
            f"({_percentage(total_passing, total_checks)} pass)"
        ),
        "enforced_checks": total_checks,
    }
    if baseline["total"] != expected_total:
        raise ValueError(
            f"scorecard baseline total must be {expected_total!r}; "
            f"got {baseline['total']!r}"
        )
    baseline_failures = {
        (int(criterion), yaml_case)
        for criterion, row in baseline["criteria"].items()
        for yaml_case in row["failing_yaml_cases"]
    }
    current_failures = {
        (mismatch.criterion, mismatch.yaml_case) for mismatch in mismatches
    }
    new_failures_by_criterion: dict[int, set[str]] = {}
    for criterion, yaml_case in current_failures - baseline_failures:
        new_failures_by_criterion.setdefault(criterion, set()).add(yaml_case)

    regressions: list[str] = []
    for criterion, yaml_cases in sorted(new_failures_by_criterion.items()):
        enforced_checks = tested_cases_by_criterion[criterion]
        allowed_failures = max(1, math.floor(enforced_checks * 0.05))
        if len(yaml_cases) <= allowed_failures:
            continue
        regressions.append(
            f"- Criterion {criterion}: {len(yaml_cases)} new failures exceed "
            f"the allowance of {allowed_failures} among {enforced_checks} "
            f"checks: {', '.join(sorted(yaml_cases))}"
        )
    return regressions


def _write_scorecard_sidecar(
    *,
    sidecar_path: Path,
    mismatches: list[_ScorecardMismatch],
    tested_cases_by_criterion: dict[int, int],
    yaml_case_count: int,
    review_duration_seconds: float | None,
    reviewer_model: str,
) -> None:
    failures_by_criterion: dict[int, set[str]] = {}
    for mismatch in mismatches:
        failures_by_criterion.setdefault(mismatch.criterion, set()).add(
            mismatch.yaml_case
        )

    criteria: dict[str, dict[str, object]] = {}
    for criterion, enforced_checks in sorted(tested_cases_by_criterion.items()):
        failing_yaml_cases = sorted(failures_by_criterion.get(criterion, set()))
        passing_checks = enforced_checks - len(failing_yaml_cases)
        criteria[str(criterion)] = {
            "success": (
                f"{passing_checks}/{enforced_checks} "
                f"({_percentage(passing_checks, enforced_checks)} pass)"
            ),
            "enforced_checks": enforced_checks,
            "failing_yaml_cases": failing_yaml_cases,
        }

    total_checks = sum(tested_cases_by_criterion.values())
    total_failures = sum(len(cases) for cases in failures_by_criterion.values())
    total_passing = total_checks - total_failures
    if review_duration_seconds is None:
        runtime = json.loads(sidecar_path.read_text(encoding="utf-8"))["runtime"]
    else:
        runtime = {
            "yaml_cases": yaml_case_count,
            "total": _duration(review_duration_seconds),
            "average_per_yaml_case": _duration(
                review_duration_seconds / yaml_case_count
            ),
        }
    sidecar = {
        "reviewer": {"model": reviewer_model},
        "total": {
            "success": (
                f"{total_passing}/{total_checks} "
                f"({_percentage(total_passing, total_checks)} pass)"
            ),
            "enforced_checks": total_checks,
        },
        "runtime": runtime,
        "criteria": criteria,
    }
    sidecar_path.write_text(_scorecard_sidecar_text(sidecar), encoding="utf-8")


def _scorecard_sidecar_text(sidecar: dict[str, object]) -> str:
    criteria = sidecar["criteria"]
    if not isinstance(criteria, dict):
        raise TypeError("scorecard sidecar criteria must be a dictionary")
    criterion_rows = list(criteria.items())
    lines = [
        "{",
        f'  "reviewer": {json.dumps(sidecar["reviewer"])},',
        f'  "total": {json.dumps(sidecar["total"])},',
        f'  "runtime": {json.dumps(sidecar["runtime"])},',
        '  "criteria": {',
    ]
    for index, (criterion, row) in enumerate(criterion_rows):
        comma = "," if index < len(criterion_rows) - 1 else ""
        lines.append(f"    {json.dumps(criterion)}: {json.dumps(row)}{comma}")
    lines.extend(["  }", "}"])
    return "\n".join(lines) + "\n"


def _read_scorecard_attestations(
    path: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    if not path.exists():
        return {}
    try:
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (json.JSONDecodeError, OSError, TypeError):
        return {}
    return {
        (str(record["yaml_case"]), str(record["test"])): record
        for record in records
        if isinstance(record, dict)
        and "yaml_case" in record
        and "test" in record
    }


def _scorecard_attestation_is_current(
    record: dict[str, object] | None,
    *,
    source_sha256: str,
    expected_scorecard: dict[int, str],
    completed_results: tuple[str, ...] = ("pass", "fail"),
) -> bool:
    if record is None:
        return False
    expected = {
        str(number): result
        for number, result in sorted(expected_scorecard.items())
    }
    actual = record.get("actual_scorecard")
    return (
        record.get("scorecard_scope") == "expected_criteria"
        and record.get("source_sha256") == source_sha256
        and record.get("linter_version") == __version__
        and record.get("expected_scorecard") == expected
        and isinstance(actual, dict)
        and set(actual) == set(expected)
        and all(result in completed_results for result in actual.values())
        and bool(record.get("reviewer"))
    )


def _write_scorecard_attestations(
    path: Path,
    records: list[dict[str, object]],
) -> None:
    path.write_text(
        "".join(
            json.dumps(record, sort_keys=True) + "\n"
            for record in sorted(
                records,
                key=lambda record: (
                    str(record["yaml_case"]),
                    str(record["test"]),
                ),
            )
        ),
        encoding="utf-8",
    )


def _record_review_start(start_path: Path, started_at: float) -> None:
    if start_path.exists():
        return
    start_path.parent.mkdir(parents=True, exist_ok=True)
    start_path.write_text(f"{started_at}\n", encoding="utf-8")


def _review_duration_seconds(
    start_path: Path,
    *,
    completed_at: float,
) -> float | None:
    if not start_path.exists():
        return None
    started_at = float(start_path.read_text(encoding="utf-8").strip())
    return max(0.0, completed_at - started_at)


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {remaining_seconds:.1f}s"


def _reviewer_model_from_environment() -> str:
    reviewer_model = os.environ.get("AGENT_REVIEW_MODEL", "").strip()
    if not reviewer_model:
        raise RuntimeError(
            "set AGENT_REVIEW_MODEL to the model and reasoning level used "
            "for anonymous review"
        )
    return reviewer_model


def _scorecard_mismatch_message(
    mismatches: list[_ScorecardMismatch],
    *,
    tested_cases_by_criterion: dict[int, int],
) -> str:
    grouped: dict[int, list[_ScorecardMismatch]] = {}
    for mismatch in mismatches:
        grouped.setdefault(mismatch.criterion, []).append(mismatch)

    rows = [
        "| Criterion | Mismatches | Enforced YAML Checks | Success Rate | Failing YAML Cases |",
        "|---:|---:|---:|---:|---|",
    ]
    for criterion, criterion_mismatches in sorted(grouped.items()):
        tested_cases = tested_cases_by_criterion[criterion]
        success_count = tested_cases - len(criterion_mismatches)
        success_rate = _percentage(success_count, tested_cases)
        yaml_cases = ", ".join(
            f"`{mismatch.yaml_case}` (expected: {mismatch.expected}, "
            f"got: {mismatch.actual})"
            for mismatch in criterion_mismatches
        )
        rows.append(
            f"| {criterion} | {len(criterion_mismatches)} | {tested_cases} | "
            f"{success_rate} | {yaml_cases} |"
        )
    enforced_checks = sum(tested_cases_by_criterion.values())
    successful_checks = enforced_checks - len(mismatches)
    rows.append(
        f"| **Total** | **{len(mismatches)}** | **{enforced_checks}** | "
        f"**{_percentage(successful_checks, enforced_checks)}** | |"
    )
    return "\n".join(
        [
            "anonymous agent-review scorecards differ from YAML expectations:",
            "",
            *rows,
            "",
            "Use $run-all-yaml-reviews to reproduce the YAML review from fresh "
            "isolated packets. Use $calibrate-agent-review-criteria to diagnose "
            "a reproduced mismatch and test generalized criterion wording.",
        ]
    )


def _percentage(numerator: int, denominator: int) -> str:
    percentage = f"{100 * numerator / denominator:.1f}".rstrip("0").rstrip(".")
    return f"{percentage}%"


def _scorecard_results(text: str) -> dict[int, str]:
    section = text.partition("## Review Scorecard")[2]
    results: dict[int, str] = {}
    for match in SCORECARD_ROW_PATTERN.finditer(section):
        criterion = int(match.group(1))
        if criterion in results:
            raise ValueError(f"duplicate scorecard criterion {criterion}")
        results[criterion] = match.group(3).strip().lower()
    return results


def _scorecard_mismatches(
    *,
    example_name: str,
    test_name: str,
    expected_scorecard: dict[int, str],
    actual_scorecard: dict[int, str],
) -> list[_ScorecardMismatch]:
    mismatches: list[_ScorecardMismatch] = []
    for criterion, expected_result in expected_scorecard.items():
        actual_result = actual_scorecard.get(criterion, "missing")
        if actual_result != expected_result:
            mismatches.append(
                _ScorecardMismatch(
                    yaml_case=example_name,
                    test_name=test_name,
                    criterion=criterion,
                    expected=expected_result,
                    actual=actual_result,
                )
            )
    return mismatches
