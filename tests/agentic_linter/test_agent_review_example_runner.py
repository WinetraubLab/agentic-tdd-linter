"""Tests in this file validate `agent_review_example_runner` located at `tests/agentic_linter/test_harness/agent_review_example_runner.py`.
`agent_review_example_runner` is responsible for orchestrating YAML-example evaluations.

Terms:
- `runner JSON`: Runner JSON is the readable `agent_review_example_runner` report at tests/agentic_linter/test_agent_review_example_runner.json. For example, every completed YAML-example evaluation overwrites this file.
- `runner JSONL`: Runner JSONL is the committed proof for criteria enforced by each YAML case at tests/agentic_linter/test_agent_review_example_runner.jsonl. For example, current proof lets CI evaluate YAML examples without `.agent.md` files.
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
        `agent_review_example_runner` produces no value when every `YAML fixture catalog` entry agrees with its expected scorecard.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Harness applies mock.patch to provide an empty artifact directory.
        1. Runner examines the `YAML fixture catalog`.
        2. Runner parses committed `runner JSONL`.
        3. Every attestation corresponds to its current YAML source and expected scorecard.
        4. Artifact directory contains zero '.agent.md' files.
        `agent_review_example_runner` evaluates the `YAML fixture catalog` as repository data rather than accepting case-specific synthetic values from this orchestration test.
        The orchestration test provides its catalog path and reviewer model.

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
        expected_result = None
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
                run_agent_review_examples(
                    examples_path=examples_path,
                    reviewer_model=reviewer_model,
                )
                packets = list(artifact_root.glob("*.agent.md"))

        self.assertEqual([], packets)

        )

        self.assertEqual(expected_result, result)

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

    def test_runner_overwrites_json(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `agent_review_example_runner` supersedes `runner JSON` after every completed YAML-example evaluation.
        Specialized usage: When the second evaluation detects a scorecard mismatch, `agent_review_example_runner` replaces prior `runner JSON`.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness applies mock.patch to replace one example.
        2. Harness initializes runner JSON with seed text.
        3. Harness completes successful evaluation.
        4. Runner replaces seeded text.
        5. Harness initializes runner JSON with new seed text.
        6. Harness completes regressing evaluation.
        7. Runner replaces seeded text before raising regression.
        Runner JSON supersedes both seeds.
        """

        example = SimpleNamespace(
            name="example",
            file_docstring='"""Verify an example."""',
            test="def test_example() -> None:\n    assert True",
            expected_scorecard={11: SimpleNamespace(result="pass")},
        )
        test_record = SimpleNamespace(name="test_example")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            anonymous_root = temporary_root / "anonymous"
            artifact_root = anonymous_root / "agentic_review_artifacts"
            artifact_root.mkdir(parents=True)
            artifact_path = artifact_root / "test_example.agent.md"
            artifact_path.write_text("completed review", encoding="utf-8")
            sidecar_path = temporary_root / "test_agent_review_example_runner.json"
            start_path = temporary_root / ".review_started_at"

            with (
                mock.patch.multiple(
                    runner_harness,
                    ANONYMOUS_ROOT=anonymous_root,
                    ARTIFACT_ROOT=artifact_root,
                    SCORECARD_BASELINE_PATH=sidecar_path,
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
                    return_value={11: "pass"},
                ),
                mock.patch.object(
                    runner_harness,
                    "_scorecard_regressions",
                    side_effect=[[], ["forced regression"]],
                ),
                mock.patch.object(
                    runner_harness,
                    "_review_duration_seconds",
                    return_value=1,
                ),
            ):
                successful_seed = "previous successful evaluation"
                sidecar_path.write_text(successful_seed, encoding="utf-8")
                start_path.write_text("started", encoding="utf-8")

                runner_harness.run_agent_review_examples(
                    examples_path=temporary_root,
                    reviewer_model="reviewer",
                )
                successful_output = sidecar_path.read_text(encoding="utf-8")

                failed_seed = "previous failed evaluation"
                sidecar_path.write_text(failed_seed, encoding="utf-8")
                start_path.write_text("started", encoding="utf-8")

                with contextlib.suppress(AssertionError):
                    runner_harness.run_agent_review_examples(
                        examples_path=temporary_root,
                        reviewer_model="reviewer",
                    )
                failed_output = sidecar_path.read_text(encoding="utf-8")

        self.assertNotIn(successful_seed, successful_output)
        self.assertNotIn(failed_seed, failed_output)


if __name__ == "__main__":
    unittest.main()
