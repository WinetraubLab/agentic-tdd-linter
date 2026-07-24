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
        )
        second_source = textwrap.dedent(
            '''\
            """Verify the second truth example."""
            """Tests in this file validate `second truth example` located at `src/second_truth.py`.
            `second truth example` is responsible for evaluating the second boolean expression.

            def test_second_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                The second truth example evaluates to true.
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

        self.assertEqual(
            {"tests/test_first.py", "tests/test_second.py"},
            approved_manifest_paths,
        )
        self.assertEqual(1, stale_lint.returncode)
        self.assertEqual({"tests/test_second.py"}, stale_manifest_paths)
        self.assertIn("missing_required_agent_md", stale_lint.stdout)
        self.assertIn("agentic-tdd-linter create-agent-md", stale_lint.stdout)
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
        4. Run `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:ci-reviewer`.
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

            lint = _run_cli(
                repo_root,
                "lint",
                "--reviewer",
                "integration:ci-reviewer",
            )

        self.assertEqual(0, lint.returncode, lint.stdout + lint.stderr)

    def test_outdated_version_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        CLI requires a new agentic review when the manifest linter version differs from the installed linter version.
        Specialized usage: The manifest linter version identifies an older release instead of the installed release.

        Verification Method: verify public function output

        Verification Detail:
        1. Create a temporary repository containing one valid test.
        2. Complete its review and record passing manifest proof with the installed CLI.
        3. Replace only the manifest record's `linter_version` value with a different version.
        4. Remove the existing '.agent.md' files to reproduce committed CI input.
        5. Run `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:version-reviewer`.
        6. Verify that lint fails, reports missing current review evidence, and prescribes `create-agent-md`.
        """

        test_source = textwrap.dedent(
            '''\
            """Verify version-sensitive review proof."""

            def test_version_sensitive_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                Current review proof remains valid for the linter release that recorded it.
                Standard usage: The installed linter records the completed review.

                Verification Method: verify public function output

                Verification Detail:
                The reviewed expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "test_version.py", test_source)
            reviewer = "integration:version-reviewer"
            _record_approved_manifest(repo_root, reviewer=reviewer)
            manifest_path = repo_root / "tests" / "agentic_review_manifest.jsonl"
            record = json.loads(manifest_path.read_text(encoding="utf-8"))
            recorded_version = record["linter_version"]
            record["linter_version"] = f"{recorded_version}-outdated"
            manifest_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            _remove_packet_directory(repo_root)

            lint = _run_cli(repo_root, "lint", "--reviewer", reviewer)

        self.assertEqual(1, lint.returncode)
        self.assertIn("missing_required_agent_md", lint.stdout)
        self.assertIn("agentic-tdd-linter create-agent-md", lint.stdout)

    def test_refresh_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI rebuilds single-test and cross-test '.agent.md' scorecards from scratch when create-agent-md uses --fresh.
        Specialized usage: Both artifact types contain completed evidence instead of pending evidence before refresh.

        Verification Method: verify public function output

        Verification Detail:
        1. Create a temporary repository containing two tests.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. The test harness mocks every review by marking it as pass.
        4. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository> --fresh`.
        5. Read every regenerated '.agent.md' file.
        6. Verify that both single-test and cross-test scorecards were rebuilt with only pending evidence.
        Generated file types are `single` and `cross`.
        Every generated file contains `| pending | Replace with review evidence. |`.
        No generated file contains prior completed evidence.
        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_creates_pending_packet`
          Justification: Deeper coverage — The lower test proves pending initialization for one packet. This test proves fresh regeneration for every single-test and cross-test packet.
        """

        first_source = textwrap.dedent(
            '''\
            """Verify the first refresh example."""

            def test_first_refresh() -> None:
                """Test Path: happy path

                Requirement Tested:
                The first refresh expression evaluates to true.
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
            """Verify the second refresh example."""

            def test_second_refresh() -> None:
                """Test Path: happy path

                Requirement Tested:
                The second refresh expression evaluates to true.
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
        self.assertEqual({"single", "cross"}, refreshed_types)
        self.assertTrue(
            all(
                "| pending | Replace with review evidence. |" in text
                for text in refreshed_contents
            )
        )
        self.assertTrue(all("| pass |" not in text for text in refreshed_contents))
        self.assertTrue(all(reviewed_evidence not in text for text in refreshed_contents))

    def test_cicd_pass_omits_packets(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `CI/CD lint` validates current manifest proof without creating an `.agent.md` directory.
        Standard usage: The repository contains current passing manifest proof before `CI/CD lint` starts.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing one valid test.
        2. Harness completes its review.
        3. Harness persists current passing proof in the manifest.
        4. Harness removes the existing '.agent.md' directory before lint.
        5. Harness invokes `CI/CD lint` using `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:ci-reviewer`.
        6. Filesystem excludes the '.agent.md' directory after lint.
        Filesystem excludes the '.agent.md' directory after lint.
        """

        test_source = textwrap.dedent(
            '''\
            """Verify approved CI packet behavior."""

            def test_approved_packet_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                Approved behavior evaluates to true.
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
            _write_source(repo_root / "tests" / "test_approved.py", test_source)
            _record_approved_manifest(
                repo_root,
                reviewer="integration:ci-reviewer",
                review_status="pass",
                review_evidence="approved packetless CI fixture",
            )
            _remove_packet_directory(repo_root)

            lint = _run_cli(
                repo_root,
                "lint",
                "--reviewer",
                "integration:ci-reviewer",
            )
            artifact_root_exists = (
                repo_root / "tests" / "agentic_review_artifacts"
            ).exists()

        self.assertFalse(artifact_root_exists)

    def test_refresh_removes_obsolete_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI create-agent-md --fresh excludes '.agent.md' files without corresponding tests.
        Specialized usage: An extra '.agent.md' file lacks a corresponding test instead of matching a current test, so CLI removes it before rebuilding current files.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing one valid test.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness introduces `test_deleted__test_deleted.agent.md` without a corresponding test.
        4. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository> --fresh`.
        5. Filesystem excludes the extra '.agent.md' file after fresh creation.
        Filesystem excludes `test_deleted__test_deleted.agent.md` after fresh creation.
        """

        test_source = textwrap.dedent(
            '''\
            """Verify obsolete-packet cleanup."""

            def test_current_packet() -> None:
                """Test Path: happy path

                Requirement Tested:
                Current packet behavior evaluates to true.
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


def _run_cli(repo_root: Path, command: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH", "")
    source_root = str(PROJECT_ROOT / "src")
    environment["PYTHONPATH"] = (
        source_root if not existing_pythonpath else source_root + os.pathsep + existing_pythonpath
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_tdd_linter.cli.main",
            command,
            "--repo-root",
            str(repo_root),
            *arguments,
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _packet_paths(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "tests" / "agentic_review_artifacts").glob("*.agent.md"))


def _complete_packets(repo_root: Path, *, status: str, evidence: str) -> None:
    for packet_path in _packet_paths(repo_root):
        packet = packet_path.read_text(encoding="utf-8")
        if status == "pass":
            packet = packet.replace(
                "| pending | Replace with review evidence. |",
                f"| pass | {evidence}. |",
            )
        else:
            packet = packet.replace(
                "| pending | Replace with review evidence. |",
                f"| fail | {evidence}. |",
                1,
            ).replace(
                "| pending | Replace with review evidence. |",
                f"| pass | {evidence}. |",
            )
        packet_path.write_text(packet, encoding="utf-8")


def _record_approved_manifest(
    repo_root: Path,
    *,
    reviewer: str,
    review_status: str,
    review_evidence: str,
) -> None:
    creation = _run_cli(repo_root, "create-agent-md")
    if creation.returncode != 0:
        raise AssertionError(creation.stdout + creation.stderr)
    _complete_packets(
        repo_root,
        status=review_status,
        evidence=review_evidence,
    )
    lint = _run_cli(repo_root, "lint", "--reviewer", reviewer)
    if lint.returncode != 0:
        raise AssertionError(lint.stdout + lint.stderr)


def _manifest_records(repo_root: Path) -> list[dict[str, str]]:
    manifest_path = repo_root / "tests" / "agentic_review_manifest.jsonl"
    return [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]


def _remove_packet_directory(repo_root: Path) -> None:
    artifact_root = repo_root / "tests" / "agentic_review_artifacts"
    for packet_path in artifact_root.glob("*.agent.md"):
        packet_path.unlink()
    if artifact_root.exists():
        artifact_root.rmdir()


if __name__ == "__main__":
    unittest.main()
