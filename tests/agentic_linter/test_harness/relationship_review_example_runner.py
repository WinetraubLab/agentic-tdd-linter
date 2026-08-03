"""Run test-relationship YAML examples through docstring-only review."""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import NamedTuple

from agentic_tdd_linter.agentic_linter.render_cross_test_agent_md_file import (
    _relationship_review_input_scope,
    _render_test_relationship_docstrings_agent_md,
)
from agentic_tdd_linter.version import __version__

from .agent_review_examples import (
    _ScorecardMismatch,
    _read_scorecard_attestations,
    _record_review_start,
    _review_duration_seconds,
    _reviewer_model_from_environment,
    _scorecard_attestation_is_current,
    _scorecard_mismatch_message,
    _scorecard_mismatches,
    _scorecard_regressions,
    _write_scorecard_attestations,
    _write_scorecard_sidecar,
)
from .relationship_review_yaml_fixture_contract import (
    DIFFERENCE_KINDS,
    EXAMPLES,
    TestRelationshipReviewExample,
    lint_test_relationship_review_examples,
    read_test_relationship_review_examples,
    relationship_review_example_files,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
ANONYMOUS_ROOT = (
    REPO_ROOT / "temporary_fixtures" / "test_relationship_review_examples"
)
ARTIFACT_ROOT = ANONYMOUS_ROOT / "agentic_review_artifacts"
REVIEW_START_PATH = ANONYMOUS_ROOT / ".review_started_at"
SCORECARD_BASELINE_PATH = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "test_relationship_review_example_runner.json"
)
SCORECARD_ATTESTATION_PATH = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "test_relationship_review_example_runner.jsonl"
)
REPORT_PATH = SCORECARD_BASELINE_PATH
_PAIR_CLASSIFICATION_PATTERN = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*"
    r"(pending|yes|no)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE | re.IGNORECASE,
)


class TestRelationshipReviewRunResult(NamedTuple):
    agent_md_files: tuple[Path, ...]


class _ExpectedReview(NamedTuple):
    test_name: str
    scorecard: dict[int, str]
    completed_results: tuple[str, ...]
    mismatch_name: str


class _PairClassification(NamedTuple):
    overlap: str
    kind: str | None


def run_test_relationship_review_examples(
    *,
    examples_path: Path = EXAMPLES,
    artifact_root: Path = ARTIFACT_ROOT,
    report_path: Path = SCORECARD_BASELINE_PATH,
    attestation_path: Path = SCORECARD_ATTESTATION_PATH,
    review_start_path: Path = REVIEW_START_PATH,
) -> TestRelationshipReviewRunResult:
    """Run every test-relationship YAML example through agentic review."""

    invocation_started_at, schema_errors = _begin_yaml_validation(examples_path)
    if schema_errors:
        raise ValueError("\n".join(schema_errors))
    examples = [
        example
        for path in relationship_review_example_files(Path(examples_path))
        for example in read_test_relationship_review_examples(path)
    ]
    duplicate_names = {
        example.name
        for example in examples
        if sum(item.name == example.name for item in examples) > 1
    }
    if duplicate_names:
        raise ValueError(
            "test-relationship YAML case names must be unique: "
            + ", ".join(sorted(duplicate_names))
        )

    attestations = _read_scorecard_attestations(Path(attestation_path))
    pending_packets: list[Path] = []
    mismatches: list[_ScorecardMismatch] = []
    completed_attestations: list[dict[str, object]] = []
    tested_cases_by_criterion: dict[int, int] = {}
    reviewer_model = ""
    for example in examples:
        packet_text = _example_packet_text(example)
        source_sha256 = hashlib.sha256(
            _relationship_review_input_scope(packet_text).encode("utf-8")
        ).hexdigest()
        review = _expected_reviews(example)[0]
        for criterion in review.scorecard:
            tested_cases_by_criterion[criterion] = (
                tested_cases_by_criterion.get(criterion, 0) + 1
            )
        current_record = attestations.get((example.name, review.test_name))
        proof_is_current = _scorecard_attestation_is_current(
            current_record,
            source_sha256=source_sha256,
            expected_scorecard=review.scorecard,
            completed_results=review.completed_results,
        )
        if proof_is_current:
            actual_scorecard = {
                int(number): str(result)
                for number, result in current_record["actual_scorecard"].items()
            }
            reviewer = current_record["reviewer"]
        else:
            artifact_path = Path(artifact_root) / f"{_safe_name(example.name)}.agent.md"
            if (
                not artifact_path.exists()
                or _relationship_review_input_scope(
                    artifact_path.read_text(encoding="utf-8")
                )
                != _relationship_review_input_scope(packet_text)
            ):
                _record_review_start(Path(review_start_path), invocation_started_at)
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(packet_text, encoding="utf-8")
            pair_classifications = _pair_classification_results(
                artifact_path.read_text(encoding="utf-8")
            )
            expected_pair = (
                example.tests[0].identifier,
                example.tests[1].identifier,
            )
            if set(pair_classifications) != {expected_pair}:
                raise ValueError(
                    f"{example.name} pair classifications do not match "
                    "the two test identifiers"
                )
            classification = pair_classifications[expected_pair]
            if _pair_classification_is_pending(classification):
                pending_packets.append(artifact_path)
                continue
            if not reviewer_model:
                reviewer_model = _reviewer_model_from_environment()
            full_actual_scorecard = {10: classification.overlap}
            if 11 in review.scorecard:
                full_actual_scorecard[11] = (
                    classification.kind
                    if classification.kind is not None
                    else "Not Applicable"
                )
            actual_scorecard = {
                criterion: full_actual_scorecard[criterion]
                for criterion in review.scorecard
            }
            reviewer = {"model": reviewer_model}

        completed_attestations.append(
            {
                "yaml_case": example.name,
                "test": review.test_name,
                "scorecard_scope": "expected_criteria",
                "source_sha256": source_sha256,
                "linter_version": __version__,
                "reviewer": reviewer,
                "expected_scorecard": {
                    str(number): result
                    for number, result in sorted(review.scorecard.items())
                },
                "actual_scorecard": {
                    str(number): result
                    for number, result in sorted(actual_scorecard.items())
                },
            }
        )
        mismatches.extend(
            _scorecard_mismatches(
                example_name=review.mismatch_name,
                test_name=review.test_name,
                expected_scorecard=review.scorecard,
                actual_scorecard=actual_scorecard,
            )
        )

    if pending_packets:
        packet_list = "\n".join(
            f"- {_display_path(path)}"
            for path in sorted(set(pending_packets))
        )
        raise RuntimeError(
            "test-relationship examples are pending; review only these "
            f"Markdown packets, then rerun the test:\n{packet_list}\n"
            "Run $run-all-yaml-reviews in test-relationship mode to complete "
            "this review."
        )

    regressions, review_duration_seconds = _finish_yaml_evaluation(
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        baseline_path=Path(report_path),
        start_path=Path(review_start_path),
    )
    _write_scorecard_attestations(
        Path(attestation_path),
        completed_attestations,
    )
    _write_scorecard_sidecar(
        sidecar_path=Path(report_path),
        mismatches=mismatches,
        tested_cases_by_criterion=tested_cases_by_criterion,
        yaml_case_count=len(examples),
        review_duration_seconds=review_duration_seconds,
        reviewer_model=_reviewer_model(completed_attestations),
    )
    if review_duration_seconds is not None:
        Path(review_start_path).unlink()
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
    return TestRelationshipReviewRunResult(
        agent_md_files=tuple(sorted(Path(artifact_root).glob("*.agent.md")))
    )


def _begin_yaml_validation(examples_path: Path) -> tuple[float, list[str]]:
    invocation_started_at = time.time()
    schema_errors = lint_test_relationship_review_examples(
        examples_path=examples_path
    )
    return invocation_started_at, schema_errors


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
    completed_at = time.time()
    review_duration_seconds = _review_duration_seconds(
        start_path,
        completed_at=completed_at,
    )
    return regressions, review_duration_seconds


def _example_packet_text(example: TestRelationshipReviewExample) -> str:
    return _render_test_relationship_docstrings_agent_md(
        [(test.identifier, test.docstring) for test in example.tests]
    )


def _expected_reviews(
    example: TestRelationshipReviewExample,
) -> tuple[_ExpectedReview, ...]:
    scorecard = {10: example.expected_requirement_overlap}
    if example.expected_difference_kind is not None:
        scorecard[11] = example.expected_difference_kind
    return (
        _ExpectedReview(
            test_name=(
                f"{example.tests[0].identifier} <> "
                f"{example.tests[1].identifier}"
            ),
            scorecard=scorecard,
            completed_results=(
                "yes",
                "no",
                "Not Applicable",
                *DIFFERENCE_KINDS,
            ),
            mismatch_name=f"{example.name}/pair",
        ),
    )


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


def _pair_classification_results(
    text: str,
) -> dict[tuple[str, str], _PairClassification]:
    classifications: dict[tuple[str, str], _PairClassification] = {}
    for match in _PAIR_CLASSIFICATION_PATTERN.finditer(text):
        pair = (match.group(1).strip(), match.group(2).strip())
        if pair in classifications:
            raise ValueError(
                "duplicate requirement-description overlap classification "
                f"for {pair[0]} and {pair[1]}"
            )
        overlap = match.group(3).strip().lower()
        raw_kind = match.group(4).strip()
        if raw_kind.lower() in {"pending", "not applicable"}:
            kind = raw_kind.title()
        elif raw_kind in DIFFERENCE_KINDS:
            kind = raw_kind
        else:
            raise ValueError(
                f"{pair[0]} and {pair[1]} kind must be pending, "
                "Not Applicable, or one supported difference kind"
            )
        classifications[pair] = _PairClassification(
            overlap=overlap,
            kind=None if kind == "Not Applicable" else kind,
        )
    if not classifications:
        raise ValueError(
            "test-relationship review packet contains no pair classifications"
        )
    return classifications


def _pair_classification_is_pending(
    classification: _PairClassification,
) -> bool:
    if classification.overlap not in {"yes", "no"}:
        return True
    if classification.overlap == "no":
        return classification.kind is not None
    return classification.kind not in DIFFERENCE_KINDS


def _safe_name(name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    if not safe_name:
        raise ValueError(
            "test-relationship YAML case name needs a filesystem-safe character"
        )
    return safe_name


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> None:
    run_test_relationship_review_examples()


if __name__ == "__main__":
    main()
