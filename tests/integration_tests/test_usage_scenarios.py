"""Verify complete command-line usage scenarios."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class UsageScenarioTests(unittest.TestCase):
    def test_nominal_review_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI completes the nominal review workflow from packet generation through manifest attestation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        1. Create a temporary repository containing one unreviewed test file.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>` to prepare review packets.
        3. The test harness mocks every review by marking it as pass.
        4. Run `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:nominal-reviewer`.
        5. Verify that the manifest records the expected path, test name, pass status, and reviewer.
        """

        test_source = textwrap.dedent(
            '''\
            """Verify arithmetic examples.

            Terms:
            - `addition`: Addition combines two numbers into their sum. For example, one plus one produces two.
            """

            def test_adds_two_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `addition` produces the sum of two numbers.
                Standard usage: The operands are positive integers.

                Verification Method: verify public function output

                Verification Detail:
                One plus one equals `2`.
                """

                assert 1 + 1 == 2
            '''
        )
        expected_test_path = "tests/test_arithmetic.py"
        expected_test_name = "test_adds_two_numbers"
        expected_reviewer = "integration:nominal-reviewer"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / expected_test_path, test_source)

            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence="nominal review passed")
            _run_cli(repo_root, "lint", "--reviewer", expected_reviewer)
            records = _manifest_records(repo_root)

        self.assertEqual(
            {
                "path": expected_test_path,
                "test": expected_test_name,
                "status": "pass",
                "reviewer": expected_reviewer,
            },
            {
                key: records[0][key]
                for key in ("path", "test", "status", "reviewer")
            },
        )

