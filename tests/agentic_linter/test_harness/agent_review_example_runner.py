"""Run repository YAML examples through anonymous agent review."""

from __future__ import annotations

import hashlib
import textwrap
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
from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)
from tests.agentic_linter.test_harness.single_test_review_yaml_fixture_contract import (
    AgentReviewExample,
    agent_review_example_files,
    criterion_titles_from_template,
    lint_agent_review_examples,
    read_agent_review_examples,
)

from .agent_review_examples import (
    _AgentReviewCase,
    _AgentReviewRunResult,
    _record_review_start,
    _scorecard_results,
    _run_yaml_reviews,
    _validate_yaml_examples,
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
SCORECARD_ATTESTATION_PATH = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "test_agent_review_example_runner.jsonl"
)


def run_agent_review_examples(
    *,
    examples_path: Path,
) -> _AgentReviewRunResult:
    """Run every YAML example in one fixture folder through agentic review."""

    invocation_started_at = _validate_yaml_examples(
        examples_path,
        lint_agent_review_examples,
    )
    examples, cases, review_inputs = _single_test_review_cases(examples_path)

    def evaluate(case: _AgentReviewCase) -> dict[int, str] | None:
        source_path, test = review_inputs[(case.yaml_case, case.test_name)]
        if not case.artifact_path.exists() or _agent_md_file_is_stale(
            test.source,
            case.artifact_path,
        ):
            _record_review_start(REVIEW_START_PATH, invocation_started_at)
            render_agent_md_file(
                source_path,
                test,
                REPO_ROOT,
                ARTIFACT_ROOT,
                score_only=True,
            )
        artifact_text = case.artifact_path.read_text(encoding="utf-8")
        if determine_agent_md_status(artifact_text) == "pending":
            return None
        results = _scorecard_results(artifact_text)
        return {
            criterion: results[criterion]
            for criterion in case.expected_scorecard
        }

    return _run_yaml_reviews(
        cases=cases,
        yaml_case_count=len(examples),
        artifact_root=ARTIFACT_ROOT,
        attestation_path=SCORECARD_ATTESTATION_PATH,
        report_path=SCORECARD_BASELINE_PATH,
        review_start_path=REVIEW_START_PATH,
        evaluate=evaluate,
        pending_message=(
            "anonymous agent-review examples are pending; review only these "
            "Markdown packets, then rerun the test:"
        ),
        completion_instruction=(
            "Run $run-all-yaml-reviews in single-test mode to complete this "
            "review."
        ),
    )


def _single_test_review_cases(
    examples_path: Path,
) -> tuple[
    list[AgentReviewExample],
    list[_AgentReviewCase],
    dict[tuple[str, str], tuple[Path, ExtractedTestRecord]],
]:
    fixture_errors: list[str] = []
    titles = criterion_titles_from_template()
    examples = [
        example
        for path in agent_review_example_files(Path(examples_path))
        for example in read_agent_review_examples(path, titles)
    ]
    cases: list[_AgentReviewCase] = []
    review_inputs: dict[
        tuple[str, str],
        tuple[Path, ExtractedTestRecord],
    ] = {}
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
            expected_scorecard = {
                number: expectation.result
                for number, expectation in example.expected_scorecard.items()
            }
            artifact_path = map_test_function_to_agent_md_file(
                source_path, REPO_ROOT, ARTIFACT_ROOT, test.name
            )
            case = _AgentReviewCase(
                yaml_case=example.name,
                test_name=test.name,
                mismatch_name=example.name,
                source_sha256=digest,
                expected_scorecard=expected_scorecard,
                completed_results=("pass", "fail"),
                artifact_path=artifact_path,
            )
            cases.append(case)
            review_inputs[(case.yaml_case, case.test_name)] = (source_path, test)
    if fixture_errors:
        raise AssertionError("\n".join(fixture_errors))
    return examples, cases, review_inputs
