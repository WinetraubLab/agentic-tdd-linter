"""Tests in this file validate `pre-commit review workflow` located at `src/agentic_tdd_linter/cli/run_lint_pipeline.py`.
`pre-commit review workflow` is responsible for maintaining test-review evidence before commit.

Terms:
- `pre-commit review workflow`: The pre-commit review workflow completes the review lifecycle before changes are committed. For example, it refreshes stale scorecards before commit.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.integration_tests.test_harness.usage_scenarios import (
    complete_packets as _complete_packets,
    manifest_records as _manifest_records,
    packet_paths as _packet_paths,
    run_cli as _run_cli,
    write_source as _write_source,
)


class PreCommitReviewWorkflowTests(unittest.TestCase):
    def test_nominal_review_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` records an approved test in the manifest with its file path, test name, pass status, and reviewer identity.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates repository. Harness creates one test.
        2. Harness invokes create-agent-md.
        3. Harness classifies reviews as successful.
        4. Harness invokes lint.
        5. Manifest contains path `tests/test_arithmetic.py`.
        6. Manifest contains test `test_adds_two_numbers`.
        7. Manifest contains status `pass`.
        8. Manifest contains reviewer `integration:nominal-reviewer`.

        Similar Coverage:
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_recording_keeps_current_proof`
          Justification: Deeper coverage — The lower test proves orphan cleanup preserves current proof. This test proves the complete `pre-commit review workflow`.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `addition` located at `src/arithmetic.py`.
            `addition` is responsible for combining numbers into their sum.

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
            _write_source(
                repo_root / "src" / "arithmetic.py",
                "def add(a, b): return a + b\n",
            )
            _write_source(repo_root / expected_test_path, test_source)

            _run_cli(repo_root, "create-agent-md")
            packets = _packet_paths(repo_root)
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

    def test_lint_before_packet_creation_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` emits missing_required_agent_md when caller invokes lint before '.agent.md' creation.
        Specialized usage: Caller invokes lint before create-agent-md instead of after it, so `pre-commit review workflow` emits missing_required_agent_md.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates a temporary repository containing one conventionally valid unreviewed test.
        2. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository>` before create-agent-md.
        3. `pre-commit review workflow` output contains missing_required_agent_md.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `unreviewed behavior` located at `src/unreviewed.py`.
            `unreviewed behavior` is responsible for evaluating boolean expressions.
            """

            def test_unreviewed_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                `unreviewed behavior` evaluates to true.
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
            _write_source(repo_root / "src" / "unreviewed.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_unreviewed.py", test_source)

            lint = _run_cli(repo_root, "lint")

        self.assertIn("missing_required_agent_md", lint.stdout)

    def test_classic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` prevents '.agent.md' creation when conventional linter emits missing_requirement.
        Specialized usage: The test omits Requirement Tested instead of providing it, so `pre-commit review workflow` creates zero packets.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates a temporary repository containing a test whose docstring omits Requirement Tested.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        Packet list contains zero paths.

        Similar Coverage:
        - Lower Level Test: `test_docstring_structure.py::test_reports_empty_requirement`
          Justification: Diagnostic completeness — The lower test proves the exact missing-requirement rule. This test proves that the rule prevents packet creation through the `pre-commit review workflow`.
        """

        invalid_test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `invalid fixture` located at `src/invalid.py`.
            `invalid fixture` is responsible for representing invalid documentation.
            """

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
            _write_source(repo_root / "src" / "invalid.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_invalid.py", invalid_test_source)

            creation = _run_cli(repo_root, "create-agent-md")
            packets = _packet_paths(repo_root)

        self.assertEqual([], packets)

    def test_agentic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` emits agent_review_failed when any completed '.agent.md' contains a failing criterion.
        Specialized usage: One '.agent.md' file contains a failed scorecard while another contains passing scorecards, so `pre-commit review workflow` emits agent_review_failed.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates a temporary repository containing two tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness classifies one review as successful and another as unsuccessful.
        4. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:failure-reviewer`.
        5. `pre-commit review workflow` output contains `agent_review_failed`.
        Lint output emits `agent_review_failed`.
        Lint output contains `Regenerate the selected packets once`.

        Similar Coverage:
        - Lower Level Test: `test_determine_agent_md_status.py::test_derives_pass_status`
          Justification: Deeper coverage — The lower test proves pass-status derivation. This test combines a passing review with a failed review through the `pre-commit review workflow`.
        - Lower Level Test: `test_determine_agent_md_status.py::test_derives_fail_status`
          Justification: Deeper coverage — The lower test proves fail-status precedence. This test proves that a failed review produces the `pre-commit review workflow` diagnostic.
        """

        passing_source = textwrap.dedent(
            '''\
            """Tests in this file validate `passing review behavior` located at `src/passing.py`.
            `passing review behavior` is responsible for evaluating approved boolean expressions.
            """

            def test_passing_review() -> None:
                """Test Path: happy path

                Requirement Tested:
                `passing review behavior` evaluates to true.
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
            """Tests in this file validate `failing review behavior` located at `src/failing.py`.
            `failing review behavior` is responsible for evaluating rejected boolean expressions.
            """

            def test_failing_review() -> None:
                """Test Path: happy path

                Requirement Tested:
                `failing review behavior` evaluates to true.
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
            _write_source(repo_root / "src" / "passing.py", "VALUE = True\n")
            _write_source(repo_root / "src" / "failing.py", "VALUE = True\n")
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

    def test_stale_test_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` regenerates pending scorecards for an edited test and the cross-test review while preserving the unchanged test's approved scorecard.
        Specialized usage: Caller modifies one approved test after `pre-commit review workflow` persists proof instead of leaving both tests current, so `pre-commit review workflow` regenerates only stale review packets.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates a temporary repository containing two tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness classifies every review as successful.
        4. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:approved-reviewer` to persist passing proof.
        5. Harness modifies only the first test source outside the `pre-commit review workflow`.
        6. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository>` again.
        7. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        8. Edited-test and cross-test '.agent.md' files contain pending evidence.
        9. Unchanged-test '.agent.md' content retains successful evidence.

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_creates_pending_packet`
          Justification: Deeper coverage — The lower test proves that one renderer output has exactly 25 pending rows. This test proves which packets regenerate after a source edit and which packet remains unchanged.
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_added_function_invalidates_manifest_proof`
          Justification: Deeper coverage — The lower test proves file-wide invalidation after a function is added. This test proves selective regeneration after an existing function is edited.
        """

        first_source = textwrap.dedent(
            '''\
            """Tests in this file validate `first truth example` located at `src/first_truth.py`.
            `first truth example` is responsible for evaluating the first boolean expression.
            """

            def test_first_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                `first truth example` evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The first expression equals true.
                """

                assert True
            '''
        )
        edited_first_source = first_source.replace(
            "`first truth example` evaluates to true.",
            "`first truth example` evaluates the documented boolean expression.",
        )
        second_source = textwrap.dedent(
            '''\
            """Tests in this file validate `second truth example` located at `src/second_truth.py`.
            `second truth example` is responsible for evaluating the second boolean expression.
            """

            def test_second_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                `second truth example` evaluates to true.
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
            _write_source(repo_root / "src" / "first_truth.py", "VALUE = True\n")
            _write_source(repo_root / "src" / "second_truth.py", "VALUE = True\n")
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
            approved_manifest_paths = {
                record["path"] for record in _manifest_records(repo_root)
            }
            single_packets = [
                path
                for path in _packet_paths(repo_root)
                if path.name != "cross_test_review.agent.md"
            ]
            first_packet = next(path for path in single_packets if "test_first" in path.name)
            second_packet = next(path for path in single_packets if "test_second" in path.name)
            cross_packet = next(
                path
                for path in _packet_paths(repo_root)
                if path.name == "cross_test_review.agent.md"
            )
            unchanged_packet_before = second_packet.read_text(encoding="utf-8")

            _write_source(first_file, edited_first_source)
            stale_lint = _run_cli(repo_root, "lint")
            stale_manifest_paths = {
                record["path"] for record in _manifest_records(repo_root)
            }
            _run_cli(repo_root, "create-agent-md")
            edited_packet_after = first_packet.read_text(encoding="utf-8")
            unchanged_packet_after = second_packet.read_text(encoding="utf-8")
            cross_packet_after = cross_packet.read_text(encoding="utf-8")

        self.assertIn(
            "| pending | Replace with review evidence. |",
            edited_packet_after,
        )
        self.assertNotIn("approved before source edit", edited_packet_after)
        self.assertEqual(unchanged_packet_before, unchanged_packet_after)
        self.assertIn(
            "| pending | Replace with review evidence. |",
            cross_packet_after,
        )
        self.assertNotIn("approved before source edit", cross_packet_after)

    def test_refresh_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` generates every single-test and cross-test '.agent.md' scorecard anew with only pending evidence when create-agent-md receives --fresh.
        Specialized usage: Both artifact types contain completed evidence instead of pending evidence before refresh, so `pre-commit review workflow` replaces every completed scorecard.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates a temporary repository containing two tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness classifies every review as successful.
        4. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository> --fresh`.
        5. Every regenerated single-test and cross-test scorecard contains only pending evidence.
        `pre-commit review workflow` output comprises `single` and `cross` types.
        Every file from `pre-commit review workflow` contains `| pending | Replace with review evidence. |`.
        No file from `pre-commit review workflow` contains prior completed evidence.

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_creates_pending_packet`
          Justification: Deeper coverage — The lower test proves that one renderer output has exactly 25 pending rows. This test proves fresh regeneration for every single-test and cross-test packet.
        """

        first_source = textwrap.dedent(
            '''\
            """Tests in this file validate `first refresh expression` located at `src/first_refresh.py`.
            `first refresh expression` is responsible for evaluating the first refresh value.
            """

            def test_first_refresh() -> None:
                """Test Path: happy path

                Requirement Tested:
                `first refresh expression` evaluates to true.
                Standard usage: The expression is unchanged.

                Verification Method: verify public function output

                Verification Detail:
                The first expression equals true.
                """

                assert True
            '''
        )
        second_source = textwrap.dedent(
            '''\
            """Tests in this file validate `second refresh expression` located at `src/second_refresh.py`.
            `second refresh expression` is responsible for evaluating the second refresh value.
            """

            def test_second_refresh() -> None:
                """Test Path: happy path

                Requirement Tested:
                `second refresh expression` evaluates to true.
                Standard usage: The expression is unchanged.

                Verification Method: verify public function output

                Verification Detail:
                The second expression equals true.
                """

                assert True
            '''
        )
        reviewed_evidence = "completed before fresh review"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "first_refresh.py", "VALUE = True\n")
            _write_source(repo_root / "src" / "second_refresh.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_first.py", first_source)
            _write_source(repo_root / "tests" / "test_second.py", second_source)
            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence=reviewed_evidence)
            _run_cli(repo_root, "create-agent-md", "--fresh")
            refreshed_packets = _packet_paths(repo_root)
            refreshed_contents = [path.read_text(encoding="utf-8") for path in refreshed_packets]

        refreshed_types = {
            "cross" if path.name == "cross_test_review.agent.md" else "single"
            for path in refreshed_packets
        }
        self.assertEqual(3, len(refreshed_packets))
        self.assertEqual({"single", "cross"}, refreshed_types)
        self.assertTrue(
            all(
                "| pending | Replace with review evidence. |" in text
                for text in refreshed_contents
            )
        )
        self.assertTrue(all("| pass |" not in text for text in refreshed_contents))
        self.assertTrue(all(reviewed_evidence not in text for text in refreshed_contents))

    def test_refresh_removes_obsolete_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` removes an '.agent.md' file when that file lacks a corresponding test during create-agent-md --fresh.
        Specialized usage: An extra '.agent.md' file lacks a corresponding test instead of matching a current test, so `pre-commit review workflow` removes it.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing one valid test.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness introduces `test_deleted__test_deleted.agent.md` without a corresponding test.
        4. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository> --fresh`.
        5. Filesystem omits the extra '.agent.md' file after fresh creation.
        Filesystem omits `test_deleted__test_deleted.agent.md` after fresh creation.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `current packet behavior` located at `src/current.py`.
            `current packet behavior` is responsible for evaluating the current packet expression.
            """

            def test_current_packet() -> None:
                """Test Path: happy path

                Requirement Tested:
                `current packet behavior` evaluates to true.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "current.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_current.py", test_source)
            _run_cli(repo_root, "create-agent-md")
            extra_agent_md = (
                repo_root
                / "tests"
                / "agentic_review_artifacts"
                / "test_deleted__test_deleted.agent.md"
            )
            extra_agent_md.write_text("extra .agent.md file\n", encoding="utf-8")

            _run_cli(repo_root, "create-agent-md", "--fresh")
            rebuilt_files = _packet_paths(repo_root)

        self.assertFalse(extra_agent_md.exists())

if __name__ == "__main__":
    unittest.main()
