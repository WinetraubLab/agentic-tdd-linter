"""Tests in this file validate `agent_review_examples` located at `tests/agentic_linter/test_harness/agent_review_examples.py`.
`agent_review_examples` is responsible for coordinating YAML-example reviews.

Terms:
- `mismatch diagnostics`: Mismatch diagnostics format YAML expectation mismatches with criterion metrics and recovery guidance. Criterion metrics contain failure count, enforced-check count, and pass rate. For example, two failures among five checks produce a 60% pass rate and a calibration recommendation.
- `calibration skill`: The calibration skill tests generalized review-criterion wording through blind experiments. For example, `$calibrate-agent-review-criteria` diagnoses a YAML scorecard mismatch.
- `pass rate`: Pass rate is the percentage of tested YAML expectations that match reviewer results. For example, seven matches among ten expectations produce a 70% pass rate.
"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from tests.agentic_linter.test_harness.agent_review_examples import (
    _ScorecardMismatch,
    _reviewer_model_from_environment,
    _scorecard_mismatch_message,
)


class AgentReviewExampleTests(unittest.TestCase):
    def test_mismatch_message_recommends_calibration_skill(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `agent_review_examples` recommends `calibration skill` in `mismatch diagnostics`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The message contains `$calibrate-agent-review-criteria`.

        Similar Coverage:
        - Higher Level Test: `test_agent_review_example_runner.py::test_anonymous_agent_review_examples`
          Justification: Diagnostic completeness — The current test isolates calibration guidance for mismatches. The higher test runs the complete YAML scorecard comparison workflow.
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
        - Higher Level Test: `test_agent_review_example_runner.py::test_anonymous_agent_review_examples`
          Justification: Diagnostic completeness — The current test isolates case-level mismatch evidence. The higher test runs the complete YAML scorecard comparison workflow.
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
        - Higher Level Test: `test_agent_review_example_runner.py::test_anonymous_agent_review_examples`
          Justification: Diagnostic completeness — The current test isolates per-criterion mismatch aggregation. The higher test runs the complete YAML scorecard comparison workflow.
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
        Total row reports a `70%` pass rate.

        Similar Coverage:
        - Higher Level Test: `test_agent_review_example_runner.py::test_anonymous_agent_review_examples`
          Justification: Diagnostic completeness — The current test isolates aggregate pass-rate calculation. The higher test runs the complete YAML scorecard comparison workflow.
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
        - Higher Level Test: `test_agent_review_example_runner.py::test_anonymous_agent_review_examples`
          Justification: Diagnostic completeness — The current test isolates criterion-specific case listings. The higher test runs the complete YAML scorecard comparison workflow.
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
        `agent_review_examples` raises RuntimeError that identifies AGENT_REVIEW_MODEL when AGENT_REVIEW_MODEL is absent.
        Specialized usage: Model loading receives no AGENT_REVIEW_MODEL identity instead of configured identity, so model loading raises RuntimeError.

        Verification Method: verify private function output

        Verification Detail:
        `mock.patch.dict` clears environment entries.
        `RuntimeError` identifies `AGENT_REVIEW_MODEL`.
        """

        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AGENT_REVIEW_MODEL"):
                _reviewer_model_from_environment()

if __name__ == "__main__":
    unittest.main()
