"""Verify deterministic mechanics for the YAML-example review harness.

The YAML files provide example test source and expected results for selected
review criteria. Tests in this module verify harness mechanics such as
mismatch reporting, baselines, timing, and result serialization.

Terms:
- `mismatch diagnostics`: Mismatch diagnostics format YAML expectation mismatches with criterion metrics and recovery guidance. Criterion metrics contain failure count, enforced-check count, and pass rate. For example, two failures among five checks produce a 60% pass rate and a calibration recommendation.
- `scorecard comparison`: Scorecard comparison checks selected expected results against reviewed scorecard results. For example, `_scorecard_mismatches` reports criterion 11 when expected fail differs from actual pass.
- `calibration skill`: The calibration skill tests generalized review-criterion wording through blind experiments. For example, `$calibrate-agent-review-criteria` diagnoses a YAML scorecard mismatch.
- `sidecar schema`: The sidecar schema contains reviewer, total, runtime, criteria, success, enforced-check count, and failing-case fields in their serialized order. For example, runtime records YAML-case count, total duration, and average duration per YAML case.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.integration_tests.test_harness.agent_review_examples import (
    _ScorecardMismatch,
    _record_review_start,
    _review_duration_seconds,
    _reviewer_model_from_environment,
    _scorecard_mismatch_message,
    _scorecard_mismatches,
    _scorecard_regressions,
    _write_scorecard_baseline,
    _write_scorecard_sidecar,
)


class AgentReviewExampleTests(unittest.TestCase):
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
