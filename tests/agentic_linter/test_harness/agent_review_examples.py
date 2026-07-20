"""Provide reusable mechanics for anonymous agent-review integration tests."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

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
            "Use $calibrate-agent-review-criteria to diagnose the mismatch and "
            "test generalized criterion wording.",
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
