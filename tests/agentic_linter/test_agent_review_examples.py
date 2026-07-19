"""Verify deterministic mechanics for the YAML-example review harness.

The YAML files provide example test source and expected results for selected
review criteria. Tests in this module verify mismatch reporting and the
runner-output lifecycle.

Terms:
- `mismatch diagnostics`: Mismatch diagnostics format YAML expectation mismatches with criterion metrics and recovery guidance. Criterion metrics contain failure count, enforced-check count, and pass rate. For example, two failures among five checks produce a 60% pass rate and a calibration recommendation.
- `scorecard comparison`: Scorecard comparison checks selected expected results against reviewed scorecard results. For example, `_scorecard_mismatches` reports criterion 11 when expected fail differs from actual pass.
- `calibration skill`: The calibration skill tests generalized review-criterion wording through blind experiments. For example, `$calibrate-agent-review-criteria` diagnoses a YAML scorecard mismatch.
"""

from __future__ import annotations

import ast
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests.agentic_linter.test_harness import agent_review_examples as review_harness
from tests.agentic_linter.test_harness.agent_review_examples import (
    REPO_ROOT,
    SCORECARD_BASELINE_PATH,
    _ScorecardMismatch,
    _reviewer_model_from_environment,
    _scorecard_mismatch_message,
    _scorecard_mismatches,
)


class AgentReviewExampleTests(unittest.TestCase):
    def test_runner_times_complete_evaluation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agentic linter measures YAML-example runtime from the start of evaluation until immediately before writing the JSON result.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        1. Parse `run_agent_review_examples` from the runner implementation.
        2. Verify that `invocation_started_at = time.time()` appears immediately before YAML validation begins.
        3. Verify that runtime calculation uses `completed_at=time.time()` immediately before `_write_scorecard_sidecar` writes the JSON result.
        """

        runner_path = (
            REPO_ROOT
            / "tests"
            / "agentic_linter"
            / "test_harness"
            / "agent_review_examples.py"
        )
        module = ast.parse(runner_path.read_text(encoding="utf-8"))
        runner = next(
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_agent_review_examples"
        )
        start_index = next(
            index
            for index, statement in enumerate(runner.body)
            if isinstance(statement, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "invocation_started_at"
                for target in statement.targets
            )
        )
        validation_index = next(
            index
            for index, statement in enumerate(runner.body)
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "lint_agent_review_examples"
                for node in ast.walk(statement)
            )
        )
        duration_index = next(
            index
            for index, statement in enumerate(runner.body)
            if isinstance(statement, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "review_duration_seconds"
                for target in statement.targets
            )
        )
        write_index = next(
            index
            for index, statement in enumerate(runner.body)
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_write_scorecard_sidecar"
                for node in ast.walk(statement)
            )
        )
        start_assignment = runner.body[start_index]
        duration_assignment = runner.body[duration_index]
        completed_at = next(
            keyword.value
            for node in ast.walk(duration_assignment)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_review_duration_seconds"
            for keyword in node.keywords
            if keyword.arg == "completed_at"
        )

        self.assertEqual(start_index + 1, validation_index)
        self.assertEqual("time.time()", ast.unparse(start_assignment.value))
        self.assertEqual(duration_index + 1, write_index)
        self.assertEqual("time.time()", ast.unparse(completed_at))

    def test_mismatch_message_recommends_calibration_skill(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Mismatch diagnostics recommend `calibration skill`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The message contains `$calibrate-agent-review-criteria`.
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
        Mismatch diagnostics distinguish expected outcomes from actual outcomes.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Message text contains ``example` (expected: fail, got: pass)``.
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
        Mismatch diagnostics quantify criterion metrics.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Criterion 32 produces `| 32 | 2 | 5 | 60% |`.
        Criterion 51 produces `| 51 | 1 | 5 | 80% |`.
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
        Mismatch diagnostics calculate total rate from all failures and checks.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Total row contains `| **Total** | **3** | **10** | **70%** | |`.
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
        Mismatch diagnostics enumerate cases per criterion with expected and actual outcomes.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Criterion 32 contains ``missing_subject` (expected: fail, got: pass)``.
        Criterion 32 contains ``missing_object` (expected: fail, got: pass)``.
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

    def test_compares_only_expected_criteria(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Scorecard comparison checks only criteria listed in the YAML expectation.
        Specialized usage: The completed '.agent.md' scorecard contains every criterion, so additional results are not treated as mismatches.

        Verification Method: verify private function output

        Verification Detail:
        YAML expectation contains criterion `11` with result `fail`.
        Reviewed scorecard additionally contains criteria `12` and `13`.
        `_scorecard_mismatches` output contains no mismatches.
        """

        mismatches = _scorecard_mismatches(
            example_name="example",
            test_name="test_example",
            expected_scorecard={11: "fail"},
            actual_scorecard={11: "fail", 12: "pass", 13: "fail"},
        )
        self.assertEqual([], mismatches)

    def test_runner_json_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Agentic linter stores populated runner results in 'tests/agentic_linter/test_agent_review_example_runner.json' under source control.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        1. Locate 'tests/agentic_linter/test_agent_review_example_runner.json'.
        2. Verify that the JSON file contains data without inspecting its schema.
        3. Verify that Git tracks the JSON file.
        JSON file is non-empty.
        `git ls-files --error-unmatch` returns `0`.
        """

        sidecar_text = SCORECARD_BASELINE_PATH.read_text(encoding="utf-8")
        tracked_query = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                str(SCORECARD_BASELINE_PATH.relative_to(REPO_ROOT)),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertTrue(sidecar_text.strip())
        self.assertEqual(0, tracked_query.returncode, tracked_query.stderr)

    def test_runner_overwrites_json(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic linter overwrites 'test_agent_review_example_runner.json' after every completed runner evaluation of YAML examples.
        Specialized usage: The second evaluation reports a regression instead of succeeding.

        Verification Method: verify public function output

        Verification Detail:
        1. Use `mock.patch` to supply one completed YAML example and force the second evaluation to report a regression.
        2. Seed the JSON file with previous evaluation text.
        3. Run one successful completed evaluation.
        4. Verify that the runner replaced the previous text with populated JSON.
        5. Seed the JSON file with different previous evaluation text.
        6. Run one completed evaluation that reports a regression.
        7. Verify that the runner replaced the previous text before raising the regression.
        JSON output is non-empty after both evaluations.
        JSON output differs from both seeded values.
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
                    review_harness,
                    ANONYMOUS_ROOT=anonymous_root,
                    ARTIFACT_ROOT=artifact_root,
                    SCORECARD_BASELINE_PATH=sidecar_path,
                    REVIEW_START_PATH=start_path,
                ),
                mock.patch.object(
                    review_harness,
                    "lint_agent_review_examples",
                    return_value=[],
                ),
                mock.patch.object(
                    review_harness,
                    "agent_review_example_files",
                    return_value=[Path("examples.yaml")],
                ),
                mock.patch.object(
                    review_harness,
                    "read_agent_review_examples",
                    return_value=[example],
                ),
                mock.patch.object(
                    review_harness,
                    "criterion_titles_from_template",
                    return_value={},
                ),
                mock.patch.object(
                    review_harness,
                    "extract_tests_from_file",
                    return_value=[test_record],
                ),
                mock.patch.object(
                    review_harness,
                    "map_test_function_to_agent_md_file",
                    return_value=artifact_path,
                ),
                mock.patch.object(
                    review_harness,
                    "_agent_md_file_is_stale",
                    return_value=False,
                ),
                mock.patch.object(
                    review_harness,
                    "determine_agent_md_status",
                    return_value="pass",
                ),
                mock.patch.object(
                    review_harness,
                    "_scorecard_results",
                    return_value={11: "pass"},
                ),
                mock.patch.object(
                    review_harness,
                    "_scorecard_regressions",
                    side_effect=[[], ["forced regression"]],
                ),
                mock.patch.object(
                    review_harness,
                    "_review_duration_seconds",
                    return_value=1,
                ),
            ):
                successful_seed = "previous successful evaluation"
                sidecar_path.write_text(successful_seed, encoding="utf-8")
                start_path.write_text("started", encoding="utf-8")

                review_harness.run_agent_review_examples(
                    examples_path=temporary_root,
                    reviewer_model="reviewer",
                )
                successful_output = sidecar_path.read_text(encoding="utf-8")

                failed_seed = "previous failed evaluation"
                sidecar_path.write_text(failed_seed, encoding="utf-8")
                start_path.write_text("started", encoding="utf-8")

                with self.assertRaises(AssertionError):
                    review_harness.run_agent_review_examples(
                        examples_path=temporary_root,
                        reviewer_model="reviewer",
                    )
                failed_output = sidecar_path.read_text(encoding="utf-8")

        self.assertTrue(successful_output.strip())
        self.assertNotEqual(successful_seed, successful_output)
        self.assertTrue(failed_output.strip())
        self.assertNotEqual(failed_seed, failed_output)

    def test_missing_reviewer_model_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Model loading emits an error when the environment omits model identity.
        Specialized usage: For model loading, environment identity is absent instead of present.

        Verification Method: verify private function output

        Verification Detail:
        `mock.patch.dict` removes every environment entry.
        `RuntimeError` identifies `AGENT_REVIEW_MODEL`.
        """

        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AGENT_REVIEW_MODEL"):
                _reviewer_model_from_environment()

if __name__ == "__main__":
    unittest.main()
