"""Tests in this file validate `agent_review_examples` located at `tests/agentic_linter/test_harness/agent_review_examples.py`.
`agent_review_examples` is responsible for coordinating YAML-example reviews.

Terms:
- `mismatch diagnostics`: Mismatch diagnostics format YAML expectation mismatches with criterion metrics and recovery guidance. Criterion metrics contain failure count, enforced-check count, and pass rate. For example, two failures among five checks produce a 60% pass rate and a calibration recommendation.
- `calibration skill`: The calibration skill tests generalized review-criterion wording through blind experiments. For example, `$calibrate-agent-review-criteria` diagnoses a YAML scorecard mismatch.
- `pass rate`: Pass rate is the percentage of tested YAML expectations that match reviewer results. For example, seven matches among ten expectations produce a 70% pass rate.
- `AGENT_REVIEW_MODEL`: AGENT_REVIEW_MODEL identifies the model that reviews YAML examples. For example, the runner rejects an absent AGENT_REVIEW_MODEL value.
- `JSONL attestation`: A JSONL attestation matches a YAML case when it contains the case's source digest and expected scorecard, the current linter version, a completed actual scorecard for the same criteria, and a reviewer.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agentic_tdd_linter.version import __version__
from tests.agentic_linter.test_harness import agent_review_examples
from tests.agentic_linter.test_harness.agent_review_examples import (
    _AgentReviewCase,
    _ScorecardMismatch,
    _finish_yaml_evaluation,
    _reviewer_model_from_environment,
    _run_yaml_reviews,
    _scorecard_mismatch_message,
    _validate_yaml_examples,
)


class AgentReviewExampleTests(unittest.TestCase):
    def test_current_jsonl_attestation_skips_evaluation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` does not evaluate a review packet when a matching `JSONL attestation` exists for the case.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Mocking makes scorecard regression comparison return no regressions.
        The evaluator receives zero calls.
        The review result contains zero packet paths.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_agent_review_examples.py::test_stale_attestation_reports_pending_packet`
          Explanation: The current test verifies `agent_review_examples` does not evaluate a review packet when a matching `JSONL attestation` exists for the case. The named test verifies `agent_review_examples` emits a pending-packet error when a `JSONL attestation` has an outdated source digest and packet evaluation remains incomplete; the current test is happy path, while the named test is failure path.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = _review_case(root)
            attestation_path = root / "attestation.jsonl"
            attestation_path.write_text(
                json.dumps(_attestation(case)) + "\n",
                encoding="utf-8",
            )
            start_path = root / ".review_started_at"
            start_path.write_text("0", encoding="utf-8")
            evaluated = False

            def evaluate(_: _AgentReviewCase) -> dict[int, str]:
                nonlocal evaluated
                evaluated = True
                return {11: "pass"}

            with mock.patch.object(
                agent_review_examples,
                "_scorecard_regressions",
                return_value=[],
            ):
                result = _run_yaml_reviews(
                    cases=[case],
                    yaml_case_count=1,
                    artifact_root=root / "artifacts",
                    attestation_path=attestation_path,
                    report_path=root / "report.json",
                    review_start_path=start_path,
                    evaluate=evaluate,
                    pending_message="pending",
                    completion_instruction="rerun",
                )

        self.assertFalse(evaluated)
        self.assertEqual((), result.agent_md_files)

    def test_stale_attestation_reports_pending_packet(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_examples` emits a pending-packet error when a `JSONL attestation` has an outdated source digest and packet evaluation remains incomplete.
        When the JSONL attestation contains an outdated source digest and packet evaluation remains incomplete, `agent_review_examples` emits the pending-packet error.

        Verification Method: verify private function output

        Verification Detail:
        The RuntimeError contains `example.agent.md`.
        The RuntimeError contains `run the YAML skill`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_agent_review_examples.py::test_current_jsonl_attestation_skips_evaluation`
          Explanation: The current test verifies `agent_review_examples` emits a pending-packet error when a `JSONL attestation` has an outdated source digest and packet evaluation remains incomplete. The named test verifies `agent_review_examples` does not evaluate a review packet when a matching `JSONL attestation` exists for the case; the current test is failure path, while the named test is happy path.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = _review_case(root)
            attestation_path = root / "attestation.jsonl"
            attestation_path.write_text(
                json.dumps(_attestation(case, source_sha256="stale")) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(RuntimeError) as raised:
                _run_yaml_reviews(
                    cases=[case],
                    yaml_case_count=1,
                    artifact_root=root / "artifacts",
                    attestation_path=attestation_path,
                    report_path=root / "report.json",
                    review_start_path=root / ".review_started_at",
                    evaluate=lambda _: None,
                    pending_message="pending",
                    completion_instruction="run the YAML skill",
                )

        self.assertIn("example.agent.md", str(raised.exception))
        self.assertIn("run the YAML skill", str(raised.exception))

    def test_validation_timer_starts_before_linting(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` starts YAML-review timing before fixture validation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Mocking records the YAML-review timer call before validation.
        Recorded event order is timer followed by validation.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_evaluation_timer_ends_after_comparison`
          Explanation: The current test verifies `agent_review_examples` starts YAML-review timing before fixture validation. The named test verifies `agent_review_examples` ends YAML-review timing after scorecard comparison and uses that time to calculate duration; both use happy path, but exercise materially different scenarios.
        """

        events: list[str] = []

        def lint(*, examples_path: Path) -> list[str]:
            events.append("validation")
            return []

        with mock.patch.object(
            agent_review_examples.time,
            "time",
            side_effect=lambda: events.append("timer") or 1.0,
        ):
            started_at = _validate_yaml_examples(Path("examples"), lint)

        self.assertEqual(1.0, started_at)
        self.assertEqual(["timer", "validation"], events)

    def test_evaluation_timer_ends_after_comparison(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` ends YAML-review timing after scorecard comparison and uses that time to calculate duration.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Mocking records scorecard comparison, timer completion, and duration calculation.
        Recorded event order is comparison, timer, then duration; returned duration is `3.0`.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_validation_timer_starts_before_linting`
          Explanation: The current test verifies `agent_review_examples` ends YAML-review timing after scorecard comparison and uses that time to calculate duration. The named test verifies `agent_review_examples` starts YAML-review timing before fixture validation; both use happy path, but exercise materially different scenarios.
        """

        events: list[str] = []

        def compare(*args: object, **kwargs: object) -> list[str]:
            events.append("comparison")
            return []

        def duration(start_path: Path, *, completed_at: float) -> float:
            events.append(f"duration:{completed_at}")
            return 3.0

        with tempfile.TemporaryDirectory() as directory:
            baseline_path = Path(directory) / "baseline.json"
            baseline_path.write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(
                    agent_review_examples,
                    "_scorecard_regressions",
                    side_effect=compare,
                ),
                mock.patch.object(
                    agent_review_examples.time,
                    "time",
                    side_effect=lambda: events.append("timer") or 4.0,
                ),
                mock.patch.object(
                    agent_review_examples,
                    "_review_duration_seconds",
                    side_effect=duration,
                ),
            ):
                _, review_duration = _finish_yaml_evaluation(
                    mismatches=[],
                    tested_cases_by_criterion={},
                    baseline_path=baseline_path,
                    start_path=Path("started"),
                )

        self.assertEqual(["comparison", "timer", "duration:4.0"], events)
        self.assertEqual(3.0, review_duration)

    def test_completed_review_replaces_outputs(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_examples` replaces the JSON report and `JSONL attestation` after successful and failed YAML reviews.
        When the second YAML review has a scorecard mismatch, `agent_review_examples` still replaces both outputs.

        Verification Method: verify private function output

        Verification Detail:
        Mocking supplies the reviewer model and successful then failed scorecard comparisons.
        The JSON report excludes its seed after each review.
        The JSONL attestation excludes its seed after each review.
        Both outputs identify reviewer model `gpt-test ultra`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_path = root / "report.json"
            attestation_path = root / "attestation.jsonl"
            start_path = root / ".review_started_at"
            case = _review_case(root)

            outputs: list[tuple[str, str]] = []
            with (
                mock.patch.dict(
                    os.environ,
                    {"AGENT_REVIEW_MODEL": "gpt-test ultra"},
                ),
                mock.patch.object(
                    agent_review_examples,
                    "_scorecard_regressions",
                    side_effect=[[], ["forced regression"]],
                ),
            ):
                for actual_result in ("pass", "fail"):
                    report_path.write_text("previous report", encoding="utf-8")
                    attestation_path.write_text(
                        "previous attestation",
                        encoding="utf-8",
                    )
                    start_path.write_text("0", encoding="utf-8")
                    with contextlib.suppress(AssertionError):
                        _run_yaml_reviews(
                            cases=[case],
                            yaml_case_count=1,
                            artifact_root=root / "artifacts",
                            attestation_path=attestation_path,
                            report_path=report_path,
                            review_start_path=start_path,
                            evaluate=lambda _: {11: actual_result},
                            pending_message="pending",
                            completion_instruction="rerun",
                        )
                    outputs.append(
                        (
                            report_path.read_text(encoding="utf-8"),
                            attestation_path.read_text(encoding="utf-8"),
                        )
                    )

        for report_text, attestation_text in outputs:
            self.assertNotIn("previous", report_text + attestation_text)
            self.assertEqual(
                {"model": "gpt-test ultra"},
                json.loads(report_text)["reviewer"],
            )
            self.assertEqual(
                {"model": "gpt-test ultra"},
                json.loads(attestation_text)["reviewer"],
            )

    def test_mismatch_message_recommends_calibration_skill(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The message contains `$calibrate-agent-review-criteria`.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`. The named test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_total_rate`
          Explanation: The current test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`. The named test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_lists_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`. The named test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_includes_case_evidence`
          Explanation: The current test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`. The named test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        """

        mismatch = _ScorecardMismatch(
            yaml_case="example",
            test_name="test_example",
            criterion=51,
            expected="fail",
            actual="pass",
        )
        message = _scorecard_mismatch_message(
            [mismatch], tested_cases_by_criterion={51: 1}
        )

        self.assertIn("$calibrate-agent-review-criteria", message)

    def test_mismatch_message_includes_case_evidence(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        One diagnostic connects `example` to expected `fail` and actual `pass`.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`. The named test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_total_rate`
          Explanation: The current test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`. The named test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_lists_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`. The named test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_recommends_calibration_skill`
          Explanation: The current test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`. The named test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        """

        mismatch = _ScorecardMismatch(
            yaml_case="example",
            test_name="test_example",
            criterion=51,
            expected="fail",
            actual="pass",
        )
        message = _scorecard_mismatch_message(
            [mismatch], tested_cases_by_criterion={51: 1}
        )

        self.assertIn("`example` (expected: fail, got: pass)", message)

    def test_mismatch_aggregates_criterion_cases(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Criterion 32 produces `| 32 | 2 | 5 | 60% |`.
        Criterion 51 produces `| 51 | 1 | 5 | 80% |`.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_total_rate`
          Explanation: The current test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`. The named test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_lists_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`. The named test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_includes_case_evidence`
          Explanation: The current test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`. The named test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_recommends_calibration_skill`
          Explanation: The current test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`. The named test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        """

        message = _scorecard_mismatch_message(
            [
                _ScorecardMismatch("missing_subject", "test_one", 32, "fail", "pass"),
                _ScorecardMismatch("missing_object", "test_two", 32, "fail", "pass"),
                _ScorecardMismatch("extra_assertion", "test_three", 51, "fail", "pass"),
            ],
            tested_cases_by_criterion={32: 5, 51: 5},
        )

        self.assertIn("| 32 | 2 | 5 | 60% |", message)
        self.assertIn("| 51 | 1 | 5 | 80% |", message)

    def test_mismatch_aggregates_total_rate(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Total row contains `3` mismatches.
        Total row contains `10` tested cases.
        Total row displays a `70%` pass rate.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases. The named test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_lists_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases. The named test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_includes_case_evidence`
          Explanation: The current test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases. The named test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_recommends_calibration_skill`
          Explanation: The current test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases. The named test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        """

        message = _scorecard_mismatch_message(
            [
                _ScorecardMismatch("one", "test_one", 32, "fail", "pass"),
                _ScorecardMismatch("two", "test_two", 32, "fail", "pass"),
                _ScorecardMismatch("three", "test_three", 51, "fail", "pass"),
            ],
            tested_cases_by_criterion={32: 5, 51: 5},
        )

        self.assertIn("| **Total** | **3** | **10** | **70%** | |", message)

    def test_mismatch_lists_criterion_cases(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Criterion 32 contains `missing_subject` with expected `fail` and actual `pass`.
        Criterion 32 contains `missing_object` with expected `fail` and actual `pass`.

        Similar Coverage:
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_criterion_cases`
          Explanation: The current test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`. The named test verifies `agent_review_examples` quantifies each criterion's failure count, enforced-check count, and `pass rate` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_aggregates_total_rate`
          Explanation: The current test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`. The named test verifies `agent_review_examples` calculates aggregate `pass rate` from all mismatches and tested cases; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_includes_case_evidence`
          Explanation: The current test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`. The named test verifies `agent_review_examples` connects one YAML expectation to one reviewer result in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_agent_review_examples.py::test_mismatch_message_recommends_calibration_skill`
          Explanation: The current test verifies `agent_review_examples` enumerates every mismatched case with its expected and actual result in `mismatch diagnostics`. The named test verifies `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`; both use happy path, but exercise materially different scenarios.
        """

        message = _scorecard_mismatch_message(
            [
                _ScorecardMismatch("missing_subject", "test_one", 32, "fail", "pass"),
                _ScorecardMismatch("missing_object", "test_two", 32, "fail", "pass"),
            ],
            tested_cases_by_criterion={32: 5},
        )

        self.assertIn("`missing_subject` (expected: fail, got: pass)", message)
        self.assertIn("`missing_object` (expected: fail, got: pass)", message)

    def test_missing_reviewer_model_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_examples` throws RuntimeError that identifies `AGENT_REVIEW_MODEL` when `AGENT_REVIEW_MODEL` is absent.
        Specialized usage: When `AGENT_REVIEW_MODEL` is absent, `agent_review_examples` throws RuntimeError.

        Verification Method: verify private function output

        Verification Detail:
        Mocking establishes an environment without `AGENT_REVIEW_MODEL`.
        The environment lacks `AGENT_REVIEW_MODEL`.
        `RuntimeError` identifies `AGENT_REVIEW_MODEL`.
        """

        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AGENT_REVIEW_MODEL"):
                _reviewer_model_from_environment()


def _review_case(root: Path) -> _AgentReviewCase:
    return _AgentReviewCase(
        yaml_case="example",
        test_name="test_example",
        mismatch_name="example",
        source_sha256="digest",
        expected_scorecard={11: "pass"},
        completed_results=("pass", "fail"),
        artifact_path=root / "artifacts" / "example.agent.md",
    )


def _attestation(
    case: _AgentReviewCase,
    *,
    source_sha256: str | None = None,
) -> dict[str, object]:
    return {
        "yaml_case": case.yaml_case,
        "test": case.test_name,
        "scorecard_scope": "expected_criteria",
        "source_sha256": source_sha256 or case.source_sha256,
        "linter_version": __version__,
        "reviewer": {"model": "gpt-test ultra"},
        "expected_scorecard": {"11": "pass"},
        "actual_scorecard": {"11": "pass"},
    }


if __name__ == "__main__":
    unittest.main()
