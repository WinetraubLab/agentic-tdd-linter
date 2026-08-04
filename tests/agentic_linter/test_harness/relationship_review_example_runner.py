"""Run test-relationship YAML examples through docstring-only review."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import NamedTuple

from agentic_tdd_linter.agentic_linter.render_cross_test_agent_md_file import (
    _relationship_review_input_scope,
    _render_test_relationship_docstrings_agent_md,
)

from .agent_review_examples import (
    _AgentReviewCase,
    _AgentReviewRunResult,
    _record_review_start,
    _run_yaml_reviews,
    _validate_yaml_examples,
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
_PAIR_CLASSIFICATION_PATTERN = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*"
    r"(pending|yes|no)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE | re.IGNORECASE,
)


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
) -> _AgentReviewRunResult:
    """Run every test-relationship YAML example through agentic review."""

    invocation_started_at = _validate_yaml_examples(
        examples_path,
        lint_test_relationship_review_examples,
    )
    examples, cases, review_inputs = _relationship_review_cases(
        examples_path,
        artifact_root,
    )

    def evaluate(case: _AgentReviewCase) -> dict[int, str] | None:
        example = review_inputs[(case.yaml_case, case.test_name)]
        packet_text = _example_packet_text(example)
        if (
            not case.artifact_path.exists()
            or _relationship_review_input_scope(
                case.artifact_path.read_text(encoding="utf-8")
            )
            != _relationship_review_input_scope(packet_text)
        ):
            _record_review_start(Path(review_start_path), invocation_started_at)
            case.artifact_path.parent.mkdir(parents=True, exist_ok=True)
            case.artifact_path.write_text(packet_text, encoding="utf-8")
        pair_classifications = _pair_classification_results(
            case.artifact_path.read_text(encoding="utf-8")
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
            return None
        scorecard = {10: classification.overlap}
        if 11 in case.expected_scorecard:
            scorecard[11] = classification.kind or "Not Applicable"
        return {
            criterion: scorecard[criterion]
            for criterion in case.expected_scorecard
        }

    return _run_yaml_reviews(
        cases=cases,
        yaml_case_count=len(examples),
        artifact_root=Path(artifact_root),
        attestation_path=Path(attestation_path),
        report_path=Path(report_path),
        review_start_path=Path(review_start_path),
        evaluate=evaluate,
        pending_message=(
            "test-relationship examples are pending; review only these "
            "Markdown packets, then rerun the test:"
        ),
        completion_instruction=(
            "Run $run-all-yaml-reviews in test-relationship mode to complete "
            "this review."
        ),
    )


def _relationship_review_cases(
    examples_path: Path,
    artifact_root: Path,
) -> tuple[
    list[TestRelationshipReviewExample],
    list[_AgentReviewCase],
    dict[tuple[str, str], TestRelationshipReviewExample],
]:
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

    cases: list[_AgentReviewCase] = []
    review_inputs: dict[tuple[str, str], TestRelationshipReviewExample] = {}
    for example in examples:
        packet_text = _example_packet_text(example)
        source_sha256 = hashlib.sha256(
            _relationship_review_input_scope(packet_text).encode("utf-8")
        ).hexdigest()
        review = _expected_reviews(example)[0]
        case = _AgentReviewCase(
            yaml_case=example.name,
            test_name=review.test_name,
            mismatch_name=review.mismatch_name,
            source_sha256=source_sha256,
            expected_scorecard=review.scorecard,
            completed_results=review.completed_results,
            artifact_path=(
                Path(artifact_root) / f"{_safe_name(example.name)}.agent.md"
            ),
        )
        cases.append(case)
        review_inputs[(case.yaml_case, case.test_name)] = example
    return examples, cases, review_inputs


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


def main() -> None:
    run_test_relationship_review_examples()


if __name__ == "__main__":
    main()
