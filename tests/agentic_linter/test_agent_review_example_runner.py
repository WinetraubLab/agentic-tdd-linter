"""Tests in this file validate `agent_review_example_runner` located at `tests/agentic_linter/test_harness/agent_review_example_runner.py`.
`agent_review_example_runner` is responsible for orchestrating YAML-example evaluations.

Terms:
- `runner JSON`: Runner JSON is the readable `agent_review_example_runner` report at tests/agentic_linter/test_agent_review_example_runner.json. For example, every completed YAML-example evaluation overwrites this file.
- `runner JSONL`: Runner JSONL is the committed proof for criteria enforced by each YAML case at tests/agentic_linter/test_agent_review_example_runner.jsonl. Current proof corresponds to every source and expected scorecard in the `YAML fixture catalog`.
- `YAML fixture catalog`: The YAML fixture catalog is repository data evaluated by `agent_review_example_runner`. For example, each entry supplies an example and its expected scorecard as the subject of evaluation.
- `timer start`: Timer start marks when measurement begins for the total time needed to run the agentic linter on the YAML examples. For example, the timer starts before YAML validation.
- `timer end`: Timer end marks when runtime measurement stops after YAML scorecards have been compared. For example, elapsed review time uses timer end as its completion timestamp.
"""

from __future__ import annotations

import contextlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests.agentic_linter.test_harness import agent_review_example_runner as runner_harness
from tests.agentic_linter.test_harness.agent_review_example_runner import (
    REPO_ROOT,
    SCORECARD_BASELINE_PATH,
    run_agent_review_examples,
)


class AgentReviewExampleRunnerTests(unittest.TestCase):
    def test_anonymous_agent_review_examples(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_example_runner` creates no '.agent.md' files when committed `runner JSONL` proof is current.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The mocked artifact directory excludes persistent artifacts.
        The `agent_review_example_runner` result contains no .agent.md paths.
        Committed `runner JSONL` corresponds to every current YAML source and expected scorecard.
        `agent_review_example_runner` evaluates the `YAML fixture catalog` as repository data rather than accepting case-specific synthetic values from this orchestration test.

        Similar Coverage:
        - Lower Level Test: `test_agent_review_yaml_fixture_contract.py::test_result_requires_explanation`
          Justification: Diagnostic completeness — The lower test isolates missing failure-explanation validation. The current test runs the complete YAML fixture catalog.
        - Lower Level Test: `test_agent_review_yaml_fixture_contract.py::test_rejects_unsupported_fields`
          Justification: Diagnostic completeness — The lower test isolates unsupported-field validation. The current test runs the complete YAML fixture catalog.
        - Lower Level Test: `test_agent_review_examples.py::test_mismatch_message_recommends_calibration_skill`
          Justification: Diagnostic completeness — The lower test isolates calibration guidance for mismatches. The current test runs the complete YAML scorecard comparison workflow.
        - Lower Level Test: `test_agent_review_examples.py::test_mismatch_message_includes_case_evidence`
          Justification: Diagnostic completeness — The lower test isolates case-level mismatch evidence. The current test runs the complete YAML scorecard comparison workflow.
        - Lower Level Test: `test_agent_review_examples.py::test_mismatch_aggregates_criterion_cases`
          Justification: Diagnostic completeness — The lower test isolates per-criterion mismatch aggregation. The current test runs the complete YAML scorecard comparison workflow.
        - Lower Level Test: `test_agent_review_examples.py::test_mismatch_aggregates_total_rate`
          Justification: Diagnostic completeness — The lower test isolates aggregate pass-rate calculation. The current test runs the complete YAML scorecard comparison workflow.
        - Lower Level Test: `test_agent_review_examples.py::test_mismatch_lists_criterion_cases`
          Justification: Diagnostic completeness — The lower test isolates criterion-specific case listings. The current test runs the complete YAML scorecard comparison workflow.
        """

        examples_relative_path = Path(
            "tests/agentic_linter/fixtures/single_test_review"
        )
        reviewer_model = "5.6 Sol Medium"
        examples_path = REPO_ROOT / examples_relative_path

        with tempfile.TemporaryDirectory() as temporary_directory:
            anonymous_root = Path(temporary_directory) / "agent_review_examples"
            artifact_root = anonymous_root / "agentic_review_artifacts"
            with mock.patch.multiple(
                runner_harness,
                ANONYMOUS_ROOT=anonymous_root,
                ARTIFACT_ROOT=artifact_root,
                REVIEW_START_PATH=anonymous_root / ".review_started_at",
            ):
                result = run_agent_review_examples(
                    examples_path=examples_path,
                    reviewer_model=reviewer_model,
                )

        self.assertEqual((), result.agent_md_files)

    def test_stale_attestation_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_example_runner` creates '.agent.md' files when `runner JSONL` attestations are stale.
        Specialized usage: When one attestation contains an outdated source hash, `agent_review_example_runner` creates one '.agent.md' file.

        Verification Method: verify public function output

        Verification Detail:
        Harness applies mock.patch to provide an isolated artifact directory and stale proof path.
        1. Harness initializes an isolated proof file from committed `runner JSONL`.
        2. Harness substitutes one source hash with a stale value.
        3. Runner evaluates the complete `YAML fixture catalog`.
        4. Artifact directory contains one '.agent.md' file.
        """

        examples_path = (
            REPO_ROOT / "tests/agentic_linter/fixtures/single_test_review"
        )
        committed_attestations = (
            REPO_ROOT
            / "tests"
            / "agentic_linter"
            / "test_agent_review_example_runner.jsonl"
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            anonymous_root = temporary_root / "agent_review_examples"
            artifact_root = anonymous_root / "agentic_review_artifacts"
            attestation_path = temporary_root / "stale.jsonl"
            records = [
                json.loads(line)
                for line in committed_attestations.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            stale_record = next(
                record
                for record in records
                if record["yaml_case"] == "ambiguous_input"
            )
            stale_record["source_sha256"] = "0" * 64
            attestation_path.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            with mock.patch.multiple(
                runner_harness,
                ANONYMOUS_ROOT=anonymous_root,
                ARTIFACT_ROOT=artifact_root,
                SCORECARD_ATTESTATION_PATH=attestation_path,
                REVIEW_START_PATH=anonymous_root / ".review_started_at",
            ):
                with contextlib.suppress(RuntimeError):
                    run_agent_review_examples(
                        examples_path=examples_path,
                        reviewer_model="5.6 Sol Medium",
                    )

            packets = list(artifact_root.glob("*.agent.md"))

        self.assertEqual(1, len(packets))

    def test_timer_start_precedes_yaml_validation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_example_runner` ensures `timer start` occurs before YAML validation begins.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        mock.patch replaces time.time and YAML validation to record their call order.
        `_begin_yaml_validation` produces `timer start` value `1.0`.
        Call order is `time`, then `validation`.
        """

        events: list[str] = []

        def record_time() -> float:
            events.append("time")
            return 1.0

        def reject_yaml(*, examples_path: Path) -> list[str]:
            events.append("validation")
            return ["invalid fixture"]

        with (
            mock.patch.object(runner_harness.time, "time", side_effect=record_time),
            mock.patch.object(
                runner_harness,
                "lint_agent_review_examples",
                side_effect=reject_yaml,
            ),
        ):
            started_at, _ = runner_harness._begin_yaml_validation(
                Path("examples")
            )

        self.assertEqual(1.0, started_at)
        self.assertEqual(["time", "validation"], events)

    def test_timer_end_follows_scorecard_comparison(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_example_runner` ensures `timer end` occurs after scorecard comparison completes.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        mock.patch replaces scorecard comparison, time.time, and duration calculation to record their call order.
        `_finish_yaml_evaluation` produces duration `3.0`.
        Duration calculation receives `timer end` value `4.0`.
        Call order is `comparison`, then `time`, then `duration`.
        """

        events: list[str] = []
        completed_values: list[float] = []

        def compare_scorecards(*args: object, **kwargs: object) -> list[str]:
            events.append("comparison")
            return []

        def record_time() -> float:
            events.append("time")
            return 4.0

        def calculate_duration(
            start_path: Path,
            *,
            completed_at: float,
        ) -> float:
            events.append("duration")
            completed_values.append(completed_at)
            return 3.0

        with (
            mock.patch.object(
                runner_harness,
                "_scorecard_regressions",
                side_effect=compare_scorecards,
            ),
            mock.patch.object(runner_harness.time, "time", side_effect=record_time),
            mock.patch.object(
                runner_harness,
                "_review_duration_seconds",
                side_effect=calculate_duration,
            ),
        ):
            _, duration = runner_harness._finish_yaml_evaluation(
                mismatches=[],
                tested_cases_by_criterion={},
                baseline_path=Path("baseline.json"),
                start_path=Path("review-started-at"),
            )

        self.assertEqual(3.0, duration)
        self.assertEqual([4.0], completed_values)
        self.assertEqual(["comparison", "time", "duration"], events)

    def test_runner_overwrites_jsonl_proof(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_example_runner` replaces `runner JSONL` after every completed YAML-example evaluation with its expected and actual scorecards.
        Specialized usage: When the second evaluation detects a scorecard mismatch, `runner JSONL` contains different expected and actual scorecards.

        Verification Method: verify private function output

        Verification Detail:
        Harness applies mock.patch to complete one successful and one regressing evaluation.
        1. Harness initializes `runner JSONL` with seed text.
        2. Harness completes a successful evaluation.
        3. Successful proof contains equal expected and actual scorecards.
        4. Harness initializes `runner JSONL` with new seed text.
        5. Harness completes a regressing evaluation.
        6. Regressing proof contains different expected and actual scorecards.
        The resulting proof excludes both seed values.
        """

        example = SimpleNamespace(
            name="example",
            file_docstring='"""Verify an example."""',
            test="def test_example() -> None:\n    assert True",
            expected_scorecard={11: SimpleNamespace(result="pass")},
        )
        test_record = SimpleNamespace(name="test_example")
        successful_seed = "previous successful evaluation"
        failed_seed = "previous failed evaluation"
        actual_scorecards = [{11: "pass"}, {11: "fail"}]
        regressions = [[], ["forced regression"]]

        outputs = _run_completed_evaluations(
            example=example,
            test_record=test_record,
            successful_seed=successful_seed,
            failed_seed=failed_seed,
            actual_scorecards=actual_scorecards,
            regressions=regressions,
        )
        successful_record = json.loads(
            outputs["successful_attestations"].splitlines()[0]
        )
        failed_record = json.loads(
            outputs["failed_attestations"].splitlines()[0]
        )

        self.assertNotIn(successful_seed, outputs["successful_attestations"])
        self.assertNotIn(failed_seed, outputs["failed_attestations"])
        self.assertEqual(
            successful_record["expected_scorecard"],
            successful_record["actual_scorecard"],
        )
        self.assertNotEqual(
            failed_record["expected_scorecard"],
            failed_record["actual_scorecard"],
        )

    def test_runner_overwrites_json_report(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_example_runner` replaces `runner JSON` after every completed YAML-example evaluation with its failing YAML cases.
        Specialized usage: When the second evaluation detects a scorecard mismatch, `runner JSON` identifies the failing YAML case.

        Verification Method: verify private function output

        Verification Detail:
        Harness applies mock.patch to complete one successful and one regressing evaluation.
        1. Harness initializes `runner JSON` with seed text.
        2. Harness completes a successful evaluation.
        3. Successful report contains zero failing YAML cases.
        4. Harness initializes `runner JSON` with new seed text.
        5. Harness completes a regressing evaluation.
        6. Regressing report contains the failing YAML case.
        The resulting report excludes both seed values.
        """

        example = SimpleNamespace(
            name="example",
            file_docstring='"""Verify an example."""',
            test="def test_example() -> None:\n    assert True",
            expected_scorecard={11: SimpleNamespace(result="pass")},
        )
        test_record = SimpleNamespace(name="test_example")
        successful_seed = "previous successful evaluation"
        failed_seed = "previous failed evaluation"
        actual_scorecards = [{11: "pass"}, {11: "fail"}]
        regressions = [[], ["forced regression"]]

        outputs = _run_completed_evaluations(
            example=example,
            test_record=test_record,
            successful_seed=successful_seed,
            failed_seed=failed_seed,
            actual_scorecards=actual_scorecards,
            regressions=regressions,
        )
        successful_report = json.loads(outputs["successful_report"])
        failed_report = json.loads(outputs["failed_report"])

        self.assertNotIn(successful_seed, outputs["successful_report"])
        self.assertNotIn(failed_seed, outputs["failed_report"])
        self.assertEqual(
            [],
            successful_report["criteria"]["11"]["failing_yaml_cases"],
        )
        self.assertEqual(
            ["example"],
            failed_report["criteria"]["11"]["failing_yaml_cases"],
        )


def _run_completed_evaluations(
    *,
    example: SimpleNamespace,
    test_record: SimpleNamespace,
    successful_seed: str,
    failed_seed: str,
    actual_scorecards: list[dict[int, str]],
    regressions: list[list[str]],
) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        anonymous_root = temporary_root / "anonymous"
        artifact_root = anonymous_root / "agentic_review_artifacts"
        artifact_root.mkdir(parents=True)
        artifact_path = artifact_root / "test_example.agent.md"
        artifact_path.write_text("completed review", encoding="utf-8")
        sidecar_path = temporary_root / "test_agent_review_example_runner.json"
        attestation_path = (
            temporary_root / "test_agent_review_example_runner.jsonl"
        )
        start_path = temporary_root / ".review_started_at"

        with (
            mock.patch.multiple(
                runner_harness,
                ANONYMOUS_ROOT=anonymous_root,
                ARTIFACT_ROOT=artifact_root,
                SCORECARD_BASELINE_PATH=sidecar_path,
                SCORECARD_ATTESTATION_PATH=attestation_path,
                REVIEW_START_PATH=start_path,
            ),
            mock.patch.object(
                runner_harness,
                "lint_agent_review_examples",
                return_value=[],
            ),
            mock.patch.object(
                runner_harness,
                "agent_review_example_files",
                return_value=[Path("examples.yaml")],
            ),
            mock.patch.object(
                runner_harness,
                "read_agent_review_examples",
                return_value=[example],
            ),
            mock.patch.object(
                runner_harness,
                "criterion_titles_from_template",
                return_value={},
            ),
            mock.patch.object(
                runner_harness,
                "extract_tests_from_file",
                return_value=[test_record],
            ),
            mock.patch.object(
                runner_harness,
                "map_test_function_to_agent_md_file",
                return_value=artifact_path,
            ),
            mock.patch.object(
                runner_harness,
                "_agent_md_file_is_stale",
                return_value=False,
            ),
            mock.patch.object(
                runner_harness,
                "determine_agent_md_status",
                return_value="pass",
            ),
            mock.patch.object(
                runner_harness,
                "_scorecard_results",
                side_effect=actual_scorecards,
            ),
            mock.patch.object(
                runner_harness,
                "_scorecard_regressions",
                side_effect=regressions,
            ),
            mock.patch.object(
                runner_harness,
                "_review_duration_seconds",
                return_value=1,
            ),
        ):
            sidecar_path.write_text(successful_seed, encoding="utf-8")
            attestation_path.write_text(successful_seed, encoding="utf-8")
            start_path.write_text("started", encoding="utf-8")

            runner_harness.run_agent_review_examples(
                examples_path=temporary_root,
                reviewer_model="reviewer",
            )
            successful_report = sidecar_path.read_text(encoding="utf-8")
            successful_attestations = attestation_path.read_text(
                encoding="utf-8"
            )

            sidecar_path.write_text(failed_seed, encoding="utf-8")
            attestation_path.write_text(failed_seed, encoding="utf-8")
            start_path.write_text("started", encoding="utf-8")

            with contextlib.suppress(AssertionError):
                runner_harness.run_agent_review_examples(
                    examples_path=temporary_root,
                    reviewer_model="reviewer",
                )
            failed_report = sidecar_path.read_text(encoding="utf-8")
            failed_attestations = attestation_path.read_text(
                encoding="utf-8"
            )

    return {
        "successful_report": successful_report,
        "successful_attestations": successful_attestations,
        "failed_report": failed_report,
        "failed_attestations": failed_attestations,
    }


if __name__ == "__main__":
    unittest.main()
