"""Tests in this file validate `agent_review_example_runner` located at `tests/agentic_linter/test_harness/agent_review_example_runner.py`.
`agent_review_example_runner` is responsible for orchestrating YAML-example evaluations.

Terms:
- `runner JSON`: Runner JSON is the `agent_review_example_runner` output at tests/agentic_linter/test_agent_review_example_runner.json. For example, every completed YAML-example evaluation overwrites this file.
- `YAML fixture catalog`: The YAML fixture catalog is repository data evaluated by `agent_review_example_runner`. For example, each entry supplies an example and its expected scorecard as the subject of evaluation.
"""

from __future__ import annotations

import ast
import contextlib
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
        1. Runner examines the `YAML fixture catalog`.
        2. Runner invokes anonymous harness.
        3. Reviewers complete files that `agent_review_example_runner` creates.
        4. Runner compares scorecards with YAML expectations.
        Review runner produces no value.
        `agent_review_example_runner` evaluates the `YAML fixture catalog` as repository data rather than accepting case-specific synthetic values from this orchestration test.
        This test provides its catalog path, reviewer model, and expected result.
        """

        examples_relative_path = Path(
            "tests/agentic_linter/fixtures/single_test_review"
        )
        reviewer_model = "5.6 Sol Medium"
        expected_result = None
        examples_path = REPO_ROOT / examples_relative_path

        result = run_agent_review_examples(
            examples_path=examples_path,
            reviewer_model=reviewer_model,
        )

        self.assertEqual(expected_result, result)

    def test_runner_times_complete_evaluation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_example_runner` calculates evaluation runtime from time.time() calls immediately before YAML validation and after scorecard comparison.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Runner assigns time.time() to the start timestamp immediately before YAML validation.
        Runner passes the start timestamp to `_record_review_start`.
        Duration calculation receives time.time() as the completion timestamp after scorecard comparison.
        """

        runner_path = (
            REPO_ROOT
            / "tests"
            / "agentic_linter"
            / "test_harness"
            / "agent_review_example_runner.py"
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
        comparison_index = next(
            index
            for index, statement in enumerate(runner.body)
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_scorecard_regressions"
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
        recorded_started_at = next(
            node.args[1]
            for node in ast.walk(runner)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_record_review_start"
        )

        self.assertEqual(start_index + 1, validation_index)
        self.assertEqual("time.time()", ast.unparse(start_assignment.value))
        self.assertEqual("invocation_started_at", ast.unparse(recorded_started_at))
        self.assertLess(comparison_index, duration_index)
        self.assertEqual("time.time()", ast.unparse(completed_at))

    def test_runner_writes_sidecar_after_timing(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_example_runner` persists `runner JSON` immediately after calculating runtime.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Runner assigns `review_duration_seconds`.
        Runner invokes `_write_scorecard_sidecar` in the next statement.
        """

        runner_path = (
            REPO_ROOT
            / "tests"
            / "agentic_linter"
            / "test_harness"
            / "agent_review_example_runner.py"
        )
        module = ast.parse(runner_path.read_text(encoding="utf-8"))
        runner = next(
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_agent_review_examples"
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

        self.assertEqual(duration_index + 1, write_index)

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

        self.assertNotEqual(successful_seed, successful_output)
        self.assertNotEqual(failed_seed, failed_output)


if __name__ == "__main__":
    unittest.main()
