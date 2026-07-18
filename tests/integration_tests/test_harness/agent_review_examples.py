"""Provide reusable mechanics for anonymous agent-review integration tests."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

from agentic_tdd_linter.agentic_linter.determine_agent_md_status import (
    _agent_md_file_is_stale,
    determine_agent_md_status,
)
from agentic_tdd_linter.agentic_linter.map_test_function_to_agent_md_file import (
    map_test_function_to_agent_md_file,
)
from agentic_tdd_linter.agentic_linter.render_agent_md_file import (
    render_agent_md_file,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)
from tests.agentic_linter.agent_review_yaml_fixture_contract import (
    agent_review_example_files,
    criterion_titles_from_template,
    lint_agent_review_examples,
    read_agent_review_examples,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
ANONYMOUS_ROOT = REPO_ROOT / "temporary_fixtures" / "agent_review_examples"
ARTIFACT_ROOT = ANONYMOUS_ROOT / "agentic_review_artifacts"
REVIEW_START_PATH = ANONYMOUS_ROOT / ".review_started_at"
SCORECARD_BASELINE_PATH = (
    REPO_ROOT / "tests" / "integration_tests" / "test_agent_review_examples.json"
)
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


def run_agent_review_examples(*, examples_path: Path, reviewer_model: str) -> None:
    """Run every YAML example in one fixture folder through agentic review."""

    reviewer_model = reviewer_model.strip()
    if not reviewer_model:
        raise ValueError("reviewer model is required")
    invocation_started_at = time.time()
    schema_errors = lint_agent_review_examples(examples_path=examples_path)
    if schema_errors:
        raise ValueError("\n".join(schema_errors))

    pending_packets: list[Path] = []
    fixture_errors: list[str] = []
    mismatches: list[_ScorecardMismatch] = []
    titles = criterion_titles_from_template()
    examples = [
        example
        for path in agent_review_example_files(Path(examples_path))
        for example in read_agent_review_examples(path, titles)
    ]
    tested_cases_by_criterion: dict[int, int] = {}
    for example in examples:
        for criterion in example.expected_scorecard:
            tested_cases_by_criterion[criterion] = (
                tested_cases_by_criterion.get(criterion, 0) + 1
            )
    for example in examples:
        source = (
            textwrap.dedent(example.file_docstring).strip()
            + "\n\n"
            + textwrap.dedent(example.test).strip()
            + "\n"
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        source_path = ANONYMOUS_ROOT / f"test_{digest}.py"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding="utf-8")
        tests = extract_tests_from_file(source_path, REPO_ROOT)
        if not tests:
            fixture_errors.append(f"{example.name}: fixture contains no tests")
            continue
        for test in tests:
            artifact_path = map_test_function_to_agent_md_file(
                source_path, REPO_ROOT, ARTIFACT_ROOT, test.name
            )
            if not artifact_path.exists() or _agent_md_file_is_stale(
                source_path, artifact_path
            ):
                _record_review_start(REVIEW_START_PATH, invocation_started_at)
                render_agent_md_file(
                    source_path, test, REPO_ROOT, ARTIFACT_ROOT
                )
            artifact_text = artifact_path.read_text(encoding="utf-8")
            if determine_agent_md_status(artifact_text) == "pending":
                pending_packets.append(artifact_path)
                continue
            mismatches.extend(
                _scorecard_mismatches(
                    example_name=example.name,
                    test_name=test.name,
                    expected_scorecard={
                        number: expectation.result
                        for number, expectation in example.expected_scorecard.items()
                    },
                    actual_scorecard=_scorecard_results(artifact_text),
                )
            )
    if pending_packets:
        packet_list = "\n".join(
            f"- {_display_path(path)}" for path in sorted(set(pending_packets))
        )
        raise RuntimeError(
            "anonymous agent-review examples are pending; review only these "
            f"Markdown packets, then rerun the test:\n{packet_list}"
        )
    if fixture_errors:
        raise AssertionError("\n".join(fixture_errors))
    regressions = _scorecard_regressions(
        mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        baseline_path=SCORECARD_BASELINE_PATH,
    )
    review_duration_seconds = _review_duration_seconds(
        REVIEW_START_PATH,
        completed_at=time.time(),
    )
    _write_scorecard_sidecar(
        sidecar_path=SCORECARD_BASELINE_PATH,
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        yaml_case_count=len(examples),
        review_duration_seconds=review_duration_seconds,
        reviewer_model=reviewer_model,
    )
    if review_duration_seconds is not None:
        REVIEW_START_PATH.unlink()
    if regressions:
        raise AssertionError(
            _scorecard_mismatch_message(
                mismatches,
                tested_cases_by_criterion=tested_cases_by_criterion,
            )
            + "\n\n"
            + "New failures exceed the committed scorecard baseline:\n"
            + "\n".join(regressions)
        )


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


def _write_scorecard_baseline(
    path: Path,
    *,
    criterion: int,
    enforced_checks: int,
    failing_yaml_cases: list[str],
) -> None:
    passing = enforced_checks - len(failing_yaml_cases)
    success = f"{passing}/{enforced_checks} ({_percentage(passing, enforced_checks)} pass)"
    path.write_text(
        json.dumps(
            {
                "total": {"success": success, "enforced_checks": enforced_checks},
                "criteria": {
                    str(criterion): {
                        "success": success,
                        "enforced_checks": enforced_checks,
                        "failing_yaml_cases": failing_yaml_cases,
                    }
                },
            }
        ),
        encoding="utf-8",
    )


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
        actual_result = actual_scorecard.get(criterion)
        if actual_result is None:
            mismatches.append(
                _ScorecardMismatch(
                    yaml_case=example_name,
                    test_name=test_name,
                    criterion=criterion,
                    expected=expected_result,
                    actual="missing",
                )
            )
        elif actual_result != expected_result:
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


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)
