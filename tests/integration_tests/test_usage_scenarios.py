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
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>` to create '.agent.md' files.
        3. Verify that the generated files include one single-test '.agent.md' file and one cross-test '.agent.md' file.
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
        CLI rejects an unreviewed test when lint runs before '.agent.md' creation.
        Specialized usage: The repository has no '.agent.md' files instead of generated files.

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
        CLI creates no '.agent.md' files when conventional lint rejects a test.
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

    def test_agentic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        CLI reports failure when one test fails agentic review and another test passes.
        Specialized usage: One '.agent.md' file contains a failed scorecard while another contains passing scorecards.

        Verification Method: verify private function output

        Verification Detail:
        1. Create a temporary repository containing two tests.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. The test harness mocks one test review as pass and the other as fail.
        4. Run `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:failure-reviewer`.
        5. Verify that CLI output reports `agent_review_failed` and prescribes one regeneration.
        Lint output emits `agent_review_failed`.
        Lint output contains `Regenerate the selected packets once`.
        """

        passing_source = textwrap.dedent(
            '''\
            """Verify a passing review example."""

            def test_passing_review() -> None:
                """Test Path: happy path

                Requirement Tested:
                Passing review behavior evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )
        failing_source = textwrap.dedent(
            '''\
            """Verify a failing review example."""

            def test_failing_review() -> None:
                """Test Path: happy path

                Requirement Tested:
                Failing review behavior evaluates to true.
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
            _write_source(repo_root / "tests" / "test_passing.py", passing_source)
            _write_source(repo_root / "tests" / "test_failing.py", failing_source)
            _run_cli(repo_root, "create-agent-md")

            _complete_packets(repo_root, status="pass", evidence="mixed review passed")
            failing_packet = next(
                path
                for path in _packet_paths(repo_root)
                if "test_failing" in path.name
            )
            failing_text = failing_packet.read_text(encoding="utf-8").replace(
                "| pass | mixed review passed. |",
                "| fail | requirement is too vague. |",
                1,
            )
            failing_packet.write_text(failing_text, encoding="utf-8")
            lint = _run_cli(repo_root, "lint", "--reviewer", "integration:failure-reviewer")

        self.assertIn("agent_review_failed", lint.stdout)
        self.assertIn("Regenerate the selected packets once", lint.stdout)

    def test_stale_test_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        CLI requires a new agentic review when an approved test becomes stale after a direct edit.
        Specialized usage: The approved test changes after manifest proof is recorded instead of remaining current.

        Verification Method: verify public function output

        Verification Detail:
        1. Create a temporary repository containing two tests.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. The test harness mocks every review by marking it as pass.
        4. Run `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:approved-reviewer` to record passing proof.
        5. Edit only the first test source outside the CLI, making its manifest proof stale.
        6. Run `agentic-tdd-linter lint --repo-root <temporary-repository>` again.
        7. Verify that lint rejects the previous proof and prescribes create-agent-md.
        8. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        9. Verify that the stale test's '.agent.md' file is pending and the current test's file retains its passing review.
        """

        first_source = textwrap.dedent(
            '''\
            """Verify the first truth example."""

            def test_first_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                The first truth example evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The first expression equals true.
                """

                assert True
            '''
        )
        edited_first_source = first_source.replace(
            "The first truth example evaluates to true.",
            "The first documented boolean expression evaluates to true.",
        )
        second_source = textwrap.dedent(
            '''\
            """Verify the second truth example."""

            def test_second_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                The second truth example evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The second expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            first_file = repo_root / "tests" / "test_first.py"
            second_file = repo_root / "tests" / "test_second.py"
            _write_source(first_file, first_source)
            _write_source(second_file, second_source)
            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence="approved before source edit")

            approved_lint = _run_cli(
                repo_root,
                "lint",
                "--reviewer",
                "integration:approved-reviewer",
            )
            single_packets = [
                path
                for path in _packet_paths(repo_root)
                if path.name != "cross_test_review.agent.md"
            ]
            first_packet = next(path for path in single_packets if "test_first" in path.name)
            second_packet = next(path for path in single_packets if "test_second" in path.name)
            unchanged_packet_before = second_packet.read_text(encoding="utf-8")

            _write_source(first_file, edited_first_source)
            stale_lint = _run_cli(repo_root, "lint")
            _run_cli(repo_root, "create-agent-md")
            edited_packet_after = first_packet.read_text(encoding="utf-8")
            unchanged_packet_after = second_packet.read_text(encoding="utf-8")

        self.assertEqual(0, approved_lint.returncode)
        self.assertEqual(1, stale_lint.returncode)
        self.assertIn("missing_required_agent_md", stale_lint.stdout)
        self.assertIn("agentic-tdd-linter create-agent-md", stale_lint.stdout)
        self.assertIn(
            "| pending | Replace with review evidence. |",
            edited_packet_after,
        )
        self.assertNotIn("approved before source edit", edited_packet_after)
        self.assertEqual(unchanged_packet_before, unchanged_packet_after)

    def test_cicd_pass_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI succeeds in CI when committed manifest proof is current.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        1. Create a temporary repository containing one valid test.
        2. Record current passing manifest proof for the test.
        3. Remove the generated '.agent.md' directory to reproduce the committed CI input state.
        4. Run `agentic-tdd-linter lint --repo-root <temporary-repository>` without a reviewer.
        5. Verify that the command exits successfully.
        CLI return code is `0`.
        """

        test_source = textwrap.dedent(
            '''\
            """Verify approved CI behavior."""

            def test_approved_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                Approved CI behavior evaluates to true.
                Standard usage: The approved expression remains unchanged.

                Verification Method: verify public function output

                Verification Detail:
                The approved expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "test_approved.py", test_source)
            _record_approved_manifest(repo_root, reviewer="integration:ci-reviewer")
            _remove_packet_directory(repo_root)

            lint = _run_cli(repo_root, "lint")

        self.assertEqual(0, lint.returncode, lint.stdout + lint.stderr)

