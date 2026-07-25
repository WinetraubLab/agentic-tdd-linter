"""Run repository YAML examples through anonymous agent review."""

from __future__ import annotations

import hashlib
import textwrap
import time
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
from tests.agentic_linter.test_harness.agent_review_yaml_fixture_contract import (
    agent_review_example_files,
    criterion_titles_from_template,
    lint_agent_review_examples,
    read_agent_review_examples,
)

from .agent_review_examples import (
    _ScorecardMismatch,
    _record_review_start,
    _review_duration_seconds,
    _scorecard_mismatch_message,
    _scorecard_mismatches,
    _scorecard_regressions,
    _scorecard_results,
    _write_scorecard_sidecar,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
ANONYMOUS_ROOT = REPO_ROOT / "temporary_fixtures" / "agent_review_examples"
ARTIFACT_ROOT = ANONYMOUS_ROOT / "agentic_review_artifacts"
REVIEW_START_PATH = ANONYMOUS_ROOT / ".review_started_at"
SCORECARD_BASELINE_PATH = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "test_agent_review_example_runner.json"
)


def run_agent_review_examples(*, examples_path: Path, reviewer_model: str) -> None:
    """Run every YAML example in one fixture folder through agentic review."""

    reviewer_model = reviewer_model.strip()
    if not reviewer_model:
        raise ValueError("reviewer model is required")
    invocation_started_at, schema_errors = _begin_yaml_validation(examples_path)
    if schema_errors:
        raise ValueError("\n".join(schema_errors))

    pending_packets: list[Path] = []
    fixture_errors: list[str] = []
    mismatches = []
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
    regressions, review_duration_seconds = _finish_yaml_evaluation(
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        baseline_path=SCORECARD_BASELINE_PATH,
        start_path=REVIEW_START_PATH,
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


def _begin_yaml_validation(examples_path: Path) -> tuple[float, list[str]]:
    invocation_started_at = time.time()
    schema_errors = lint_agent_review_examples(examples_path=examples_path)
    return invocation_started_at, schema_errors


def _finish_yaml_evaluation(
    *,
    mismatches: list[_ScorecardMismatch],
    tested_cases_by_criterion: dict[int, int],
    baseline_path: Path,
    start_path: Path,
) -> tuple[list[str], float | None]:
    regressions = _scorecard_regressions(
        mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        baseline_path=baseline_path,
    )
    completed_at = time.time()
    review_duration_seconds = _review_duration_seconds(
        start_path,
        completed_at=completed_at,
    )
    return regressions, review_duration_seconds


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)
