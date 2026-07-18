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
        3. Verify that packet storage contains one single-test packet and one cross-test packet.
        4. The test harness mocks every review by marking it as pass.
        5. Run `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:nominal-reviewer`.
        6. Verify that the manifest records the expected path, test name, pass status, and reviewer.
        Packet types are `single` and `cross`.
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
            packets = _packet_paths(repo_root)
            _complete_packets(repo_root, status="pass", evidence="nominal review passed")
            _run_cli(repo_root, "lint", "--reviewer", expected_reviewer)
            records = _manifest_records(repo_root)

        packet_types = {
            "cross" if path.name == "cross_test_review.agent.md" else "single"
            for path in packets
        }
        self.assertEqual({"single", "cross"}, packet_types)
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

    def test_lint_before_packet_creation_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        CLI rejects an unreviewed test when lint runs before review-packet creation.
        Specialized usage: The repository has no review packets instead of generated packets.

        Verification Method: verify private function output

        Verification Detail:
        1. Create a temporary repository containing one conventionally valid unreviewed test.
        2. Run `agentic-tdd-linter lint --repo-root <temporary-repository>` before create-agent-md.
        3. Read the CLI result and generated packet paths.
        4. Verify that lint fails.
        5. Verify that CLI output reports the missing review packet.
        6. Verify that CLI output prescribes create-agent-md.
        7. Verify that lint creates no packets.
        """

        test_source = textwrap.dedent(
            '''\
            """Verify an unreviewed test fixture."""

            def test_unreviewed_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                Unreviewed behavior evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "test_unreviewed.py", test_source)

            lint = _run_cli(repo_root, "lint")
            packets = _packet_paths(repo_root)

        self.assertEqual(1, lint.returncode)
        self.assertIn("missing_required_agent_md", lint.stdout)
        self.assertIn("agentic-tdd-linter create-agent-md", lint.stdout)
        self.assertEqual([], packets)

    def test_classic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        CLI creates no review packets when conventional lint rejects a test.
        Specialized usage: The test omits Requirement Tested instead of providing it.

        Verification Method: verify private function output

        Verification Detail:
        1. Create a temporary repository containing a test whose docstring omits Requirement Tested.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Read the generated packet paths.
        4. Verify that the command created no `.agent.md` packets.
        Packet list is empty.
        """

        invalid_test_source = textwrap.dedent(
            '''\
            """Verify an invalid test fixture."""

            def test_invalid_documentation() -> None:
                """Test Path: failure path

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "test_invalid.py", invalid_test_source)

            _run_cli(repo_root, "create-agent-md")
            packets = _packet_paths(repo_root)

        self.assertEqual([], packets)

